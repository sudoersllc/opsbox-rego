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
                str,
                Field(default=None, description="AWS access key ID. Omit to use CLI credentials.", required=True),
            ]
            aws_secret_access_key: Annotated[
                str,
                Field(default=None, description="AWS secret access key. Omit to use CLI credentials.", required=True),
            ]
            aws_region: Annotated[
                str | None,
                Field(
                    description="AWS region(s), separated by a comma",
                    required=False,
                    default=None,
                ),
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
    def gather_data(self) -> Result:
        """
        Gathers data related to AWS EFS and returns it in a format that can be used by the rego policy.

        Returns:
            Result: EFS data in a format that can be used by the rego policy.
        """
        credentials = self.credentials
        regions = credentials["aws_region"]  # Get the regions from the credentials

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

            # Create EFS and CloudWatch clients for the given region
            try:
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
                        max(
                            datapoint["Average"] for datapoint in metrics["Datapoints"]
                        ),
                        2,
                    )
                except Exception as e:
                    logger.error(
                        f"Error retrieving percent I/O limit for EFS {file_system_id}: {e}"
                    )
                    return 0

            try:
                response = efs_client.describe_file_systems()
                for fs in response["FileSystems"]:
                    file_system_id = fs["FileSystemId"]
                    logger.trace(f"Getting info for EFS {file_system_id}")

                    percent_io_limit = get_percent_io_limit(file_system_id)

                    with lock:
                        efs_data.append(
                            {
                                "Name": fs["Name"],
                                "Id": file_system_id,
                                "PercentIOLimit": percent_io_limit,
                            }
                        )
                logger.debug(
                    f"Gathered EFS data for {len(response['FileSystems'])} file systems in {region}",
                )
            except Exception as e:
                logger.error(f"Error gathering EFS info: {e}")

        # Process each region in a separate thread
        for region in regions:
            logger.info(f"Gathering EFS data for region {region}...")
            region_thread = threading.Thread(target=process_region, args=(region,))
            region_threads.append(region_thread)
            region_thread.start()

        # Wait for all threads to complete
        for region_thread in region_threads:
            region_thread.join()

        # Prepare the data in a format that can be consumed by Rego
        rego_ready_data = {"input": {"efss": efs_data}}
        logger.success(
            f"Found info for {len(efs_data)} EFS file systems from {len(regions)} region(s).",
            extra={"efs_data": efs_data},
        )
        item = Result(
            relates_to="efs",
            result_name="aws_efs_data",
            result_description="Structured EFS data.",
            formatted="",
            details=rego_ready_data,
        )
        return item
