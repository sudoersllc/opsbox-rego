from pluggy import HookimplMarker
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import boto3
from loguru import logger
import concurrent.futures
from typing import Annotated
import threading


from opsbox import Result


# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")


class RDSProvider:
    """Plugin for gathering data related to AWS RDS instances.

    Attributes:
        S3 (boto3.client): The boto3 client for S3.
        credentials (dict): A dictionary containing AWS access key, secret access key, and region.
    """

    @hookimpl
    def grab_config(self):
        """Return the plugin's configuration."""

        class RDSConfig(BaseModel):
            """Configuration for the AWS RDS plugin."""

            aws_access_key_id: Annotated[str,Field(..., description="AWS access key ID", required=True)]
            aws_secret_access_key: Annotated[str,Field(..., description="AWS secret access key", required=True)]
            aws_region: Annotated[
                str | None, Field(description="AWS-Region", required=False, default=None)
            ]

        return RDSConfig

    @hookimpl
    def activate(self) -> None:
        """Initialize the plugin."""
        logger.trace("Activating the RDS plugin")

    @hookimpl
    def set_data(self, model: type[BaseModel]) -> None:
        """Set the data for the plugin based on the model."""
        logger.trace("Setting data for RDS plugin...")
        self.credentials = model.model_dump()

    @hookimpl
    def gather_data(self):
        """
        Gathers data related to AWS RDS instances.

        Returns:
            dict: A dictionary containing the gathered data in the following format:
                "input": {
                        "rds_instances": [
                            {
                                "InstanceIdentifier": "instance-id",
                                "InstanceType": "db.t2.micro",
                                "Region": "us-west-1a",
                                "AllocatedStorage": 20,
                                "CPUUtilization": 5.5,
                                "Connections": 150,
                                "StorageUtilization": 80
                            },
                            ...
                        ]
                    }
        """

        def get_rds_instances(rds_client: boto3.client):
            """Retrieve information about RDS instances."""
            instances = []
            paginator = rds_client.get_paginator("describe_db_instances")
            for page in paginator.paginate():
                for instance in page["DBInstances"]:
                    instances.append(
                        {
                            "InstanceIdentifier": instance["DBInstanceIdentifier"],
                            "InstanceType": instance["DBInstanceClass"],
                            "Region": instance["AvailabilityZone"],
                            "AllocatedStorage": instance["AllocatedStorage"],
                            "Engine": instance["Engine"],
                        }
                    )
            return instances

        def get_rds_snapshots(rds_client: boto3.client):
            """Retrieve information about RDS snapshots."""
            snapshots = []
            paginator = rds_client.get_paginator("describe_db_snapshots")
            for page in paginator.paginate():
                for snapshot in page["DBSnapshots"]:
                    snapshots.append(
                        {
                            "SnapshotIdentifier": snapshot["DBSnapshotIdentifier"],
                            "InstanceIdentifier": snapshot["DBInstanceIdentifier"],
                            "SnapshotCreateTime": snapshot["SnapshotCreateTime"].isoformat(),
                            "AllocatedStorage": snapshot["AllocatedStorage"],
                            "StorageType": snapshot["StorageType"],
                        }
                    )
            return snapshots

        def get_cloudwatch_metric(
            instance_id: str, metric_name: str, statistic: str, period: int, cloudwatch_client: boto3.client
        ):
            """Retrieve CloudWatch metrics for a given instance."""
            end_time = datetime.now()
            start_time = end_time - timedelta(days=7)

            response = cloudwatch_client.get_metric_statistics(
                Namespace="AWS/RDS",
                MetricName=metric_name,
                Dimensions=[{"Name": "DBInstanceIdentifier", "Value": instance_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=period,
                Statistics=[statistic],
            )

            datapoints = response["Datapoints"]
            return sum(datapoint[statistic] for datapoint in datapoints) / len(datapoints) if datapoints else 0

        def get_storage_utilization(instance_id, cloudwatch_client, allocated_storage):
            """Calculate the storage utilization for a given instance."""
            avg_free_storage = get_cloudwatch_metric(
                instance_id, "FreeStorageSpace", "Average", 86400, cloudwatch_client
            )
            avg_free_storage_gb = avg_free_storage / (1024**3)  # Convert bytes to GB
            used_storage_gb = allocated_storage - avg_free_storage_gb
            return round((used_storage_gb / allocated_storage) * 100)

        # Initialize boto3 clients for RDS and CloudWatch




        def process_region(region):


            if self.credentials["aws_access_key_id"] is None:
                # Use the instance profile credentials
                rds_client = boto3.client("rds", region_name=region)
                cloudwatch_client = boto3.client("cloudwatch", region_name=region)
            else:
                rds_client = boto3.client(
                    "rds",
                    aws_access_key_id=self.credentials["aws_access_key_id"],
                    aws_secret_access_key=self.credentials["aws_secret_access_key"],
                    region_name=region,
                )

                cloudwatch_client = boto3.client(
                    "cloudwatch",
                    aws_access_key_id=self.credentials["aws_access_key_id"],
                    aws_secret_access_key=self.credentials["aws_secret_access_key"],
                    region_name=region,
                )
            instances = get_rds_instances(rds_client)
            snapshots.append(get_rds_snapshots(rds_client))
        # Retrieve RDS instances

            

            # Use a ThreadPoolExecutor to gather metrics concurrently
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = []
                for instance in instances:
                    futures.append(
                        executor.submit(
                            get_cloudwatch_metric,
                            instance["InstanceIdentifier"],
                            "CPUUtilization",
                            "Average",
                            3600,
                            cloudwatch_client,
                        )
                    )
                    futures.append(
                        executor.submit(
                            get_cloudwatch_metric,
                            instance["InstanceIdentifier"],
                            "DatabaseConnections",
                            "Sum",
                            86400,
                            cloudwatch_client,
                        )
                    )
                    futures.append(
                        executor.submit(
                            get_storage_utilization,
                            instance["InstanceIdentifier"],
                            cloudwatch_client,
                            instance["AllocatedStorage"],
                        )
                    )

                # Collect results and populate instance data
                for i, instance in enumerate(instances):
                    instance["CPUUtilization"] = futures[i * 3].result()
                    instance["Connections"] = futures[i * 3 + 1].result()
                    instance["StorageUtilization"] = futures[i * 3 + 2].result()
                    instance_data.append(instance)



        credentials = self.credentials

        if credentials["aws_region"] is None:
            logger.info("Gathering data for IAM...")

            # Use the specified region or default to "us-west-1"
            region = credentials["aws_region"] or "us-west-1"
            
            if credentials["aws_access_key_id"] is None:
                # Use the instance profile credentials
                region_client = boto3.client("ec2", region_name=region)
                regions = [region["RegionName"] for region in region_client.describe_regions()["Regions"]]
            else:
                try:
                    region_client = boto3.client(
                        "ec2",
                        aws_access_key_id=credentials["aws_access_key_id"],
                        aws_secret_access_key=credentials["aws_secret_access_key"],
                        region_name=region,
                    )
                    regions = [region["RegionName"] for region in region_client.describe_regions()["Regions"]]

                except Exception as e:
                    logger.error(f"Error creating IAM client: {e}")
                    return Result(
                        relates_to="aws_data",
                        result_name="aws_iam_data",
                        result_description="Structured IAM data using.",
                        formatted="Error creating IAM client.",
                        details={},
                    )

        else:
            regions = credentials["aws_region"].split(",")

        region_threads = []  # List to store threads
        instance_data = []  # List to store instances
        snapshots = []  # List to store snapshots


        for region in regions:
            region_thread = threading.Thread(target=process_region, args=(region,))
            region_threads.append(region_thread)
            region_thread.start()

        # Wait for all threads to complete
        for region_thread in region_threads:
            region_thread.join()


        rego_ready_data = {
            "input": {
                "rds_instances": instance_data,
                "rds_snapshots": snapshots,
                "date": datetime.now().isoformat() + "Z",
            }
        }
        item = Result(
            relates_to="rds",
            result_name="rds_instances",
            result_description="RDS Instances",
            details=rego_ready_data,
            formatted="",
        )
        logger.success("Successfully gathered data for RDS instances.", extra = {"output_data": rego_ready_data})
        return item
