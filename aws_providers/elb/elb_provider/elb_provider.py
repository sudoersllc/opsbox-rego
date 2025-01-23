from pluggy import HookimplMarker
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import boto3
from loguru import logger
import threading
from opsbox import Result
from typing import Annotated

# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")


class elbProvider:
    """Plugin for gathering data related to AWS S3 (buckets, objects, and storage classes).

    Attributes:
        elb_client (boto3.client): The boto3 client for ELB.
        credentials (dict): A dictionary containing AWS access key, secret access key, and region.
    """

    @hookimpl
    def grab_config(self) -> BaseModel:
        """Return the plugin's configuration.

        Returns:
            ELBConfig: The configuration model for the plugin."""

        class ELBConfig(BaseModel):
            """Configuration for the AWS ELB plugin.

            Attributes:
                aws_access_key_id (str): AWS access key ID.
                aws_secret_access_key (str): AWS secret access key.
                aws_region (str): AWS region."""

            aws_access_key_id: Annotated[str, Field(..., description="AWS access key ID", required=True)]
            aws_secret_access_key: Annotated[str, Field(..., description="AWS secret access key", required=True)]
            aws_region: Annotated[str | None, Field(description="AWS-Region", required=False, default=None)]

        return ELBConfig

    @hookimpl
    def activate(self) -> None:
        """Initialize the plugin."""
        logger.trace("Activating the ELB plugin")

    @hookimpl
    def set_data(self, model: type[BaseModel]) -> None:
        """Set the data for the plugin based on the model.

        Args:
            model (BaseModel): The model containing the data for the plugin."""
        logger.trace("Setting data for ELB plugin...")
        self.credentials = model.model_dump()

    @hookimpl
    def gather_data(self) -> Result:
        """
        Gathers data related to AWS ELB (Classic, Application, and Network Load Balancers).

        Returns:
            Result: The data in a format that can be used by the rego policy.
        """
        credentials = self.credentials
        logger.info(credentials["aws_region"])

        # If no region is provided, get all regions
        if credentials["aws_region"] is None:
            region_client = boto3.client(
                "ec2",
                aws_access_key_id=credentials["aws_access_key_id"],
                aws_secret_access_key=credentials["aws_secret_access_key"],
                region_name="us-west-1",
            )

            regions = [region["RegionName"] for region in region_client.describe_regions()["Regions"]]
            logger.info(f"Regions: {regions}")

        else:
            regions = credentials["aws_region"].split(",")

        elb_data = []  # List to store load balancer details
        region_threads = []  # List to store threads

        # helper function to process each region
        def process_region(region):
            """Process the given region and gather data.

            Args:
                region (str): The region to process.
            """
            credentials = self.credentials
            logger.debug(f"Gathering data for region {region}...")

            # Initialize boto3 clients with provided credentials
            elb_client = boto3.client(
                "elb",
                aws_access_key_id=credentials["aws_access_key_id"],
                aws_secret_access_key=credentials["aws_secret_access_key"],
                region_name=region,
            )
            elbv2_client = boto3.client(
                "elbv2",
                aws_access_key_id=credentials["aws_access_key_id"],
                aws_secret_access_key=credentials["aws_secret_access_key"],
                region_name=region,
            )
            cw_client = boto3.client(
                "cloudwatch",
                aws_access_key_id=credentials["aws_access_key_id"],
                aws_secret_access_key=credentials["aws_secret_access_key"],
                region_name=region,
            )

            end_time = datetime.now()
            start_time = end_time - timedelta(days=30)

            def get_request_count(load_balancer_name: str, namespace: str, dimension_name: str) -> int:
                """Get the total request count for the given load balancer.

                Args:
                    load_balancer_name (str): The name of the load balancer.
                    namespace (str): The namespace for the metric.
                    dimension_name (str): The dimension name for the metric.
                    
                Returns:
                    int: The total request count."""
                try:
                    metrics = cw_client.get_metric_statistics(
                        Namespace=namespace,
                        MetricName="RequestCount",
                        Dimensions=[{"Name": dimension_name, "Value": load_balancer_name}],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=86400,
                        Statistics=["Sum"],
                    )
                    if not metrics["Datapoints"]:
                        logger.warning(f"No request count data for {load_balancer_name}")
                        return 0
                    return sum([datapoint["Sum"] for datapoint in metrics["Datapoints"]])
                except Exception as e:
                    logger.error(f"Error retrieving request count for {load_balancer_name}: {e}")
                    return 0

            def get_classic_load_balancer_instance_health(elb_client, load_balancer_name:str) -> list:
                """Get the health status of instances behind a classic load balancer.
                
                Args:
                    elb_client (boto3.client): The boto3 client for ELB.
                    load_balancer_name (str): The name of the load balancer.
                    
                Returns:
                    list: The list of instances and their health status."""
                try:
                    response = elb_client.describe_instance_health(LoadBalancerName=load_balancer_name)
                    instance_health = []
                    for instance in response["InstanceStates"]:
                        instance_health.append({"InstanceId": instance["InstanceId"], "State": instance["State"], "Description": instance["Description"]})
                    return instance_health
                except Exception as e:
                    logger.error(f"Error retrieving instance health for classic load balancer {load_balancer_name}: {e}")
                    return []

            def get_error_rate(load_balancer_name: str, namespace: str, dimension_name:str) -> int:
                """Get the total error rate for the given load balancer.
                
                Args:
                    load_balancer_name (str): The name of the load balancer.
                    namespace (str): The namespace for the metric.
                    dimension_name (str): The dimension name for the metric.
                    
                Returns:
                    int: The total error rate."""
                try:
                    metrics = cw_client.get_metric_statistics(
                        Namespace=namespace,
                        MetricName="HTTPCode_ELB_5XX_Count",
                        Dimensions=[{"Name": dimension_name, "Value": load_balancer_name}],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=86400,
                        Statistics=["Sum"],
                    )
                    if not metrics["Datapoints"]:
                        logger.warning(f"No error rate data for {load_balancer_name}")
                        return 0
                    return sum([datapoint["Sum"] for datapoint in metrics["Datapoints"]])
                except Exception as e:
                    logger.error(f"Error retrieving error rate for {load_balancer_name}: {e}")
                    return 0

            def process_classic_load_balancers():
                """Process Classic Load Balancers and gather data.
                
                Returns:
                    list: The list of classic load balancer data."""
                try:
                    logger.info("Getting classic load balancer info...")
                    response = elb_client.describe_load_balancers()
                    for lb in response["LoadBalancerDescriptions"]:
                        lb_name = lb["LoadBalancerName"]
                        logger.debug(f"Getting info for classic load balancer {lb_name}")

                        # Get request count, error rate, and instance health
                        request_count = get_request_count(lb_name, "AWS/ELB", "LoadBalancerName")
                        error_rate = get_error_rate(lb_name, "AWS/ELB", "LoadBalancerName")
                        instance_health = get_classic_load_balancer_instance_health(elb_client, lb_name)

                        elb_data.append(
                            {
                                "Type": "Classic",
                                "Name": lb_name,
                                "RequestCount": request_count,
                                "ErrorRate": error_rate,
                                "CreatedTime": lb["CreatedTime"].strftime("%Y-%m-%dT%H:%M:%SZ"),
                                "AvailabilityZones": lb["AvailabilityZones"],
                                "Instances": [instance["InstanceId"] for instance in lb["Instances"]],
                                "SecurityGroups": lb["SecurityGroups"],
                                "Scheme": lb["Scheme"],
                                "DNSName": lb["DNSName"],
                                "InstanceHealth": instance_health,  # Include instance health here
                            }
                        )
                    logger.success("Classic load balancer info collected successfully.")
                except Exception as e:
                    logger.error(f"Error gathering classic load balancer info: {e}")

            def get_alb_nlb_instance_health(elbv2_client, target_group_arn: str) -> list:
                """Get the health status of instances behind an ALB or NLB.
                
                Args:
                    elbv2_client (boto3.client): The boto3 client for ELBv2.
                    target_group_arn (str): The ARN of the target group."""
                try:
                    response = elbv2_client.describe_target_health(TargetGroupArn=target_group_arn)
                    instance_health = []
                    for target in response["TargetHealthDescriptions"]:
                        instance_health.append(
                            {"InstanceId": target["Target"]["Id"], "State": target["TargetHealth"]["State"], "Description": target["TargetHealth"].get("Description", "No description available")}
                        )
                    return instance_health
                except Exception as e:
                    logger.error(f"Error retrieving instance health for target group {target_group_arn}: {e}")
                    return []

            def process_application_network_load_balancers():
                """Process Application and Network Load Balancers and gather data."""
                try:
                    logger.info("Getting application and network load balancer info...")
                    response = elbv2_client.describe_load_balancers()
                    for lb in response["LoadBalancers"]:
                        lb_arn = lb["LoadBalancerArn"]
                        lb_name = lb["LoadBalancerName"]
                        logger.info(f"Getting info for {lb['Type']} load balancer {lb_name}")

                        # Get request count, error rate, and target group info
                        request_count = get_request_count(lb_arn, "AWS/ApplicationELB", "LoadBalancer")
                        error_rate = get_error_rate(lb_arn, "AWS/ApplicationELB", "LoadBalancer")
                        target_groups = elbv2_client.describe_target_groups(LoadBalancerArn=lb_arn)

                        for tg in target_groups["TargetGroups"]:
                            target_group_arn = tg["TargetGroupArn"]

                            # Get instance health
                            instance_health = get_alb_nlb_instance_health(elbv2_client, target_group_arn)

                            # Format the data
                            elb_data.append(
                                {
                                    "Type": lb["Type"],
                                    "Name": lb_name,
                                    "RequestCount": request_count,
                                    "ErrorRate": error_rate,
                                    "CreatedTime": lb["CreatedTime"].strftime("%Y-%m-%dT%H:%M:%SZ"),
                                    "AvailabilityZones": [zone["ZoneName"] for zone in lb["AvailabilityZones"]],
                                    "SecurityGroups": lb.get("SecurityGroups", []),
                                    "Scheme": lb["Scheme"],
                                    "DNSName": lb["DNSName"],
                                    "State": lb["State"]["Code"],
                                    "VpcId": lb["VpcId"],
                                    "InstanceHealth": instance_health,  # Include instance health here
                                }
                            )
                    logger.success("Application and network load balancer info collected successfully.")
                except Exception as e:
                    logger.error(f"Error gathering application and network load balancer info: {e}")

            # Process Application and Network Load Balancers
            classic_thread = threading.Thread(target=process_classic_load_balancers)
            alb_nlb_thread = threading.Thread(target=process_application_network_load_balancers)

            # Start the threads
            classic_thread.start()
            alb_nlb_thread.start()

            # Wait for the threads to finish
            classic_thread.join()
            alb_nlb_thread.join()

        # Process each region in a separate thread
        for region in regions:
            region_thread = threading.Thread(target=process_region, args=(region,))
            region_threads.append(region_thread)
            region_thread.start()

        # Wait for all threads to complete
        for region_thread in region_threads:
            region_thread.join()
        
        # Prepare the data in a format that can be consumed by Rego
        rego_ready_data = {"input": {"elbs": elb_data}}
        logger.success("ELB data gathered successfully.")
        logger.trace(f"ELB data: {rego_ready_data}")
        item = Result(
            relates_to="elb",
            result_name="elb_info",
            result_description="ELB Information",
            details=rego_ready_data,
            formatted="",
        )
        return item
