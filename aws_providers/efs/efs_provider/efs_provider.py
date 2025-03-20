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


class efsProvider:
    """Plugin for gathering data related to EFS

    Attributes:
        efs_client (boto3.client): The boto3 client for EFS.
        credentials (dict): A dictionary containing AWS access key, secret access key, and region.
    """

    @hookimpl
    def grab_config(self) -> BaseModel:
        """Return the plugin's configuration.

        Returns:
            EFSConfig: The configuration model for the plugin."""

        class EFSConfig(BaseModel):
            """Configuration for the AWS EFS plugin.

            Attributes:
                aws_access_key_id (str): AWS access key ID.
                aws_secret_access_key (str): AWS secret access key.
                aws_region (str): AWS region."""

            aws_access_key_id: Annotated[
                str, Field(..., description="AWS access key ID", required=True)
            ]
            aws_secret_access_key: Annotated[
                str, Field(..., description="AWS secret access key", required=True)
            ]
            aws_region: Annotated[
                str | None,
                Field(description="AWS-Region", required=False, default=None),
            ]

        return EFSConfig

    @hookimpl
    def activate(self) -> None:
        """Initialize the plugin."""
        logger.trace("Activating the EFS plugin")

    @hookimpl
    def set_data(self, model: type[BaseModel]) -> None:
        """Set the data for the plugin based on the model.

        Args:
            model (BaseModel): The model containing the data for the plugin."""
        logger.trace("Setting data for EFS plugin...")
        self.credentials = model.model_dump()

    @hookimpl
    def gather_data(self) -> Result:
        """
        Gathers data related to AWS EFS and returns it in a format that can be used by the rego policy.

        Returns:
            Result: EFS data in a format that can be used by the rego policy.
        """
        credentials = self.credentials

        # If no region is provided, get all regions
        if credentials["aws_region"] is None:
            logger.info("Gathering regions for EFS...")
            credentials = self.credentials

            # Use the specified region or default to "us-west-1"
            region = credentials["aws_region"] or "us-west-1"

            if credentials["aws_access_key_id"] is None:
                # Use the instance profile credentials
                region_client = boto3.client("ec2", region_name=region)
            else:
                try:
                    region_client = boto3.client(
                        "ec2",
                        aws_access_key_id=credentials["aws_access_key_id"],
                        aws_secret_access_key=credentials["aws_secret_access_key"],
                        region_name=region,
                    )
                    regions = [
                        region["RegionName"]
                        for region in region_client.describe_regions()["Regions"]
                    ]

                except Exception as e:
                    logger.error(f"Error creating EFS client: {e}")
                    return Result(
                        relates_to="aws_efs",
                        result_name="awfs_efs_info",
                        result_description="Structured EFS data.",
                        formatted="Error finding regions.",
                        details={},
                    )

        else:
            regions = credentials["aws_region"].split(",")

        efs_data = []  # List to store efs data
        region_threads = []  # List to store threads

        lock = threading.Lock()

        # helper function to process each region
        def process_region(region):
            """Process the given region and gather data.

            Args:
                region (str): The region to process.
            """
            credentials = self.credentials
            logger.debug(f"Gathering EFS data for region {region}...")

            try:
                # Initialize boto3 clients with provided credentials
                if (
                    credentials["aws_access_key_id"] is None
                    or credentials["aws_secret_access_key"] is None
                ):
                    efs_client = boto3.client("efs", region_name=region)
                    cw_client = boto3.client("cloudwatch", region_name=region)
                else:
                    efs_client = boto3.client(
                        "efs",
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
            except Exception as e:
                logger.error(f"Error creating EFS clients: {e}")
                return

            end_time = datetime.now()
            start_time = end_time - timedelta(days=7)

            def get_percent_io_limit(file_system_id: str) -> int:
                """Get the percent of I/O limit for the given EFS.

                Args:
                    file_system_id (str): The ID of the EFS.

                Returns:
                    int: The percent of I/O limit."""
                try:
                    metrics = cw_client.get_metric_statistics(
                        Namespace="AWS/EFS",
                        MetricName="PercentIOLimit",
                        Dimensions=[
                            {"Name": "FileSystemId", "Value": file_system_id},
                        ],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=3600,
                        Statistics=["Average"],
                        Unit="Percent",
                    )
                    if not metrics["Datapoints"]:
                        logger.warning(f"No percent_io_limit data for {file_system_id}")
                        return 0
                    return round(
                        max(datapoint["Average"] for datapoint in metrics["Datapoints"]),
                        2,
                    )
                except Exception as e:
                    logger.error(
                        f"Error retrieving percent I/O limit for EFS {file_system_id}: {e}"
                    )
                    return 0

            try:
                logger.info(f"Getting EFS info for {region}")
                response = efs_client.describe_file_systems()
                for fs in response["FileSystems"]:
                    file_system_id = fs["FileSystemId"]
                    logger.debug(f"Getting info for EFS {file_system_id}")

                    percent_io_limit = get_percent_io_limit(file_system_id)

                    with lock:
                        efs_data.append(
                            {
                                "Name": fs["Name"],
                                "Id": file_system_id,
                                "PercentIOLimit": percent_io_limit,
                            }
                        )
                logger.success("EFS info collected successfully.")
            except Exception as e:
                logger.error(f"Error gathering EFS info: {e}")

        # Process each region in a separate thread
        for region in regions:
            region_thread = threading.Thread(target=process_region, args=(region,))
            region_threads.append(region_thread)
            region_thread.start()

        # Wait for all threads to complete
        for region_thread in region_threads:
            region_thread.join()

        # Prepare the data in a format that can be consumed by Rego
        rego_ready_data = {"input": {"efss": efs_data}}
        logger.success("EFS data gathered successfully.")
        logger.trace(f"EFS data: {rego_ready_data}")
        item = Result(
            relates_to="efs",
            result_name="efs_info",
            result_description="EFS Information",
            details=rego_ready_data,
            formatted="",
        )
        return item
