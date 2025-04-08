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
        rds_client (boto3.client): The boto3 client for RDS.
        credentials (dict): A dictionary containing AWS access key, secret access key, and region.
    """

    @hookimpl
    def grab_config(self):
        """Return the plugin's configuration."""

        class RDSConfig(BaseModel):
            """Configuration for the AWS RDS plugin."""

            aws_access_key_id: Annotated[
                str,
                Field(description="AWS access key ID", required=False, default=None),
            ]
            aws_secret_access_key: Annotated[
                str,
                Field(
                    description="AWS secret access key", required=False, default=None
                ),
            ]
            aws_region: Annotated[
                str | None,
                Field(description="AWS-Region", required=False, default=None),
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
        self.credentials["aws_region"] = self.get_regions(model)

    def get_regions(self, model: type[BaseModel]) -> type[BaseModel]:
        """Get the regions from the model.

        Args:
            model (type[BaseModel]): The model containing the data for the plugin.

        Returns:
            type[BaseModel]: The model containing the data for the plugin.
        """

        # Check if the region is provided in the model
        regions = [] if model.aws_region is None else model.aws_region.split(",")
        default_region = "us-west-1"

        # If no regions are provided, gather regions from AWS
        try:
            if not regions:
                logger.info("No region(s) provided. Gathering regions.")
                if (
                    model.aws_access_key_id is None
                    or model.aws_secret_access_key is None
                ):
                    region_client = boto3.client("ec2", region_name=default_region)
                else:
                    region_client = boto3.client(
                        "ec2",
                        aws_access_key_id=model.aws_access_key_id,
                        aws_secret_access_key=model.ws_secret_access_key,
                        region_name=default_region,
                    )
                regions = [
                    r["RegionName"] for r in region_client.describe_regions()["Regions"]
                ]

                logger.success(
                    f"Found {len(regions)} region(s).",
                    extra={"regions": regions},
                )
        except Exception as e:
            logger.exception(
                f"Error gathering regions: {e}. Using default region {default_region}."
            )

        # If no regions are found, return an error
        if not regions:
            logger.warning(f"No regions found. Using default region {default_region}.")
            regions = [default_region]

        return regions

    @hookimpl
    def gather_data(self):
        """
        Gathers data related to AWS RDS instances.

        Returns:
            Result: A result object containing the gathered data formatted for Rego.
        """

        def get_rds_instances(rds_client: boto3.client):
            """Retrieve information about RDS instances."""
            logger.trace("Gathering RDS instances...")
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
            logger.trace("Gathering RDS snapshots...")
            snapshots = []
            paginator = rds_client.get_paginator("describe_db_snapshots")
            for page in paginator.paginate():
                for snapshot in page["DBSnapshots"]:
                    snapshots.append(
                        {
                            "SnapshotIdentifier": snapshot["DBSnapshotIdentifier"],
                            "InstanceIdentifier": snapshot["DBInstanceIdentifier"],
                            "SnapshotCreateTime": snapshot[
                                "SnapshotCreateTime"
                            ].isoformat(),
                            "AllocatedStorage": snapshot["AllocatedStorage"],
                            "StorageType": snapshot["StorageType"],
                        }
                    )
            return snapshots

        def get_cloudwatch_metric(
            instance_id: str,
            metric_name: str,
            statistic: str,
            period: int,
            cloudwatch_client: boto3.client,
        ):
            """Retrieve CloudWatch metrics for a given instance."""
            logger.trace(
                f"Gathering CloudWatch metric {metric_name} for {instance_id}..."
            )
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
            return (
                sum(datapoint[statistic] for datapoint in datapoints) / len(datapoints)
                if datapoints
                else 0
            )

        def get_storage_utilization(instance_id, cloudwatch_client, allocated_storage):
            """Calculate the storage utilization for a given instance."""
            logger.trace(
                f"Calculating storage utilization for {instance_id} with allocated storage {allocated_storage}..."
            )
            avg_free_storage = get_cloudwatch_metric(
                instance_id, "FreeStorageSpace", "Average", 86400, cloudwatch_client
            )
            avg_free_storage_gb = avg_free_storage / (1024**3)  # Convert bytes to GB
            used_storage_gb = allocated_storage - avg_free_storage_gb
            return round((used_storage_gb / allocated_storage) * 100)

        # Shared data structures and a lock for thread safety.
        instance_data = []  # List to store instance details across regions.
        snapshots = []  # List to store snapshots across regions.
        data_lock = threading.Lock()

        region_threads = []  # List to store threads for each region.

        def process_region(region):
            if self.credentials["aws_access_key_id"] is None:
                # Use the instance profile credentials.
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
            # Append snapshots safely.
            with data_lock:
                snapshots.append(get_rds_snapshots(rds_client))

            # Use a ThreadPoolExecutor to gather CloudWatch metrics concurrently.
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

                # Collect results and populate instance data.
                for i, instance in enumerate(instances):
                    instance["CPUUtilization"] = futures[i * 3].result()
                    instance["Connections"] = futures[i * 3 + 1].result()
                    instance["StorageUtilization"] = futures[i * 3 + 2].result()
                    # Append to shared instance_data list in a thread-safe manner.
                    with data_lock:
                        instance_data.append(instance)

        # Start a thread for each region.
        regions = self.credentials["aws_region"]
        for region in regions:
            logger.debug(f"Starting thread for region {region}...")
            region_thread = threading.Thread(target=process_region, args=(region,))
            region_threads.append(region_thread)
            region_thread.start()

        # Wait for all region threads to complete.
        for region_thread in region_threads:
            region_thread.join()

        logger.success(
            f"Successfully gathered data for {len(instance_data)} RDS instances and {len(snapshots)} snapshots in {len(regions)} region(s).",
            extra={"regions": regions},
        )

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
        logger.success(
            "Successfully gathered data for RDS instances.",
            extra={"output_data": rego_ready_data},
        )
        return item
