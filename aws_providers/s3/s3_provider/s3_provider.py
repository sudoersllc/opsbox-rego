from pluggy import HookimplMarker
from pydantic import BaseModel, Field
from datetime import datetime
import boto3
from loguru import logger
import threading
from opsbox import Result
from typing import Annotated

hookimpl = HookimplMarker("opsbox")


class S3Provider:
    """Plugin for gathering data related to AWS S3 (buckets, objects, and storage classes).

    Attributes:
        s3_client (boto3.client): The boto3 client for S3
        credentials (dict): AWS credentials'
    """

    @hookimpl
    def grab_config(self):
        """Return the plugin's configuration.
        Attributes:
            aws_access_key_id: str: AWS access key ID
            aws_secret_access_key: str: AWS secret access key
            aws_region: str: AWS region
        Returns:
            S3Config: Configuration for the AWS S3 plugin
        """

        class S3Config(BaseModel):
            """Configuration for the AWS S3 plugin."""

            aws_access_key_id: Annotated[
                str,
                Field(description="AWS access key ID", default=None),
            ]
            aws_secret_access_key: Annotated[
                str,
                Field(
                    description="AWS secret access key",
                    default=None,
                ),
            ]
            aws_region: Annotated[
                str | None,
                Field(description="AWS-Region", default=None),
            ]
            object_count_threshold: Annotated[
                int,
                Field(description="Object count threshold", default=30),
            ]
            bucket_count_threshold: Annotated[
                int,
                Field(description="Bucket count threshold", default=100),
            ]

        return S3Config

    @hookimpl
    def activate(self) -> None:
        """Initialize the plugin."""
        logger.trace("Activating the S3 plugin")

    @hookimpl
    def set_data(self, model: type[BaseModel]) -> None:
        """Set the data for the plugin based on the model.

        Attributes:
            model: type[BaseModel]: The model containing the plugin's data
        """
        logger.trace("Setting data for S3 plugin...")
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
        regions = (
            []
            if model.aws_region is None
            else model.aws_region.split(",")
        )
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
                    r["RegionName"]
                    for r in region_client.describe_regions()["Regions"]
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
        """Gather data related to AWS S3 (buckets, objects, and storage classes).

        Returns:
            Result: A result object containing the gathered data formatted for Rego
        """
        logger.info("Gathering data for S3 plugin...")

        all_buckets = []  # Shared list to store bucket details
        all_objects = []  # Shared list to store object details
        processed_buckets = 0  # Shared counter for processed buckets

        # Create a lock to protect shared data
        data_lock = threading.Lock()

        credentials = self.credentials
        regions = credentials["aws_region"]  # Get the regions from the credentials

        # Convert thresholds to integers (they may come in as strings)
        object_count_threshold = int(credentials["object_count_threshold"])
        bucket_count_threshold = int(credentials["bucket_count_threshold"])


        region_threads = []  # Threads for each region

        def process_region(region):
            # Create an S3 client for this region.
            if credentials["aws_access_key_id"] is None:
                s3_client = boto3.client("s3", region_name=region)
            else:
                s3_client = boto3.client(
                    "s3",
                    aws_access_key_id=credentials["aws_access_key_id"],
                    aws_secret_access_key=credentials["aws_secret_access_key"],
                    region_name=region,
                )

            response = s3_client.list_buckets()  # List all buckets
            logger.debug(f"Found {len(response['Buckets'])} buckets in region {region}")
            buckets = response["Buckets"]
            bucket_threads = []

            def process_bucket(bucket):
                nonlocal processed_buckets
                bucket_name = bucket["Name"]
                bucket_details = {
                    "BucketName": bucket_name,
                    "CreationDate": bucket["CreationDate"].isoformat(),
                    "LastModified": None,
                }

                # Safely check the bucket count and update shared state
                with data_lock:
                    if processed_buckets >= bucket_count_threshold:
                        return
                    processed_buckets += 1
                    all_buckets.append(bucket_details)

                most_recent_last_modified = None
                thresholded_buckets = []
                try:
                    paginator = s3_client.get_paginator("list_objects_v2")
                    bucket_storage_classes = set()
                    object_counter = 0
                    for page in paginator.paginate(Bucket=bucket_name):
                        for obj in page.get("Contents", []):
                            if object_counter >= object_count_threshold:
                                logger.trace(
                                    f"Reached object count threshold for bucket {bucket_name}, skipping remaining objects"
                                )
                                thresholded_buckets.append(bucket_name)
                                break
                            # Gather object details
                            object_details = {
                                "Key": obj["Key"],
                                "LastModified": obj["LastModified"].timestamp(),
                                "StorageClass": obj.get("StorageClass", "STANDARD"),
                            }
                            bucket_storage_classes.add(object_details["StorageClass"])
                            if (
                                most_recent_last_modified is None
                                or obj["LastModified"] > most_recent_last_modified
                            ):
                                most_recent_last_modified = obj["LastModified"]
                                with data_lock:
                                    bucket_details["LastModified"] = obj[
                                        "LastModified"
                                    ].timestamp()
                            with data_lock:
                                all_objects.append(object_details)
                            object_counter += 1

                        if object_counter >= object_count_threshold:
                            break
                    
                    if len(thresholded_buckets) > 0:
                        logger.warning(
                            f"{len(thresholded_buckets)} buckets have over {object_count_threshold} objects, skipped remaining objects.", extra = {"buckets": thresholded_buckets}
                        )
                    inferred_storage_class = (
                        bucket_storage_classes.pop()
                        if len(bucket_storage_classes) == 1
                        else "MIXED"
                    )
                    # Update the bucket's storage class in the shared list
                    with data_lock:
                        for b in all_buckets:
                            if b["BucketName"] == bucket_name:
                                b["StorageClass"] = inferred_storage_class

                    with data_lock:
                        if processed_buckets >= bucket_count_threshold:
                            logger.warning(
                                "Reached bucket count threshold, skipping remaining buckets"
                            )
                            return
                        
                except Exception as e:
                    logger.error(f"Error listing objects for bucket {bucket_name}: {e}")

            # Process buckets concurrently
            for bucket in buckets:
                with data_lock:
                    if processed_buckets >= bucket_count_threshold:
                        break
                thread = threading.Thread(target=process_bucket, args=(bucket,))
                bucket_threads.append(thread)
                thread.start()

            for thread in bucket_threads:
                thread.join()

        # Start a thread for each region.
        for region in regions:
            logger.debug(f"Processing region {region}...")
            region_thread = threading.Thread(target=process_region, args=(region,))
            region_threads.append(region_thread)
            region_thread.start()

        # Wait for all region threads to finish.
        for region_thread in region_threads:
            region_thread.join()

        # Prepare the data in a format that can be consumed by Rego.
        rego_ready_data = {
            "input": {
                "objects": all_objects,
                "buckets": [
                    {
                        "name": bucket["BucketName"],
                        "storage_class": bucket.get("StorageClass", "STANDARD"),
                        "last_modified": bucket.get("LastModified", None),
                    }
                    for bucket in all_buckets
                ],
                "current_time": int(datetime.now().timestamp()),
            }
        }

        item = Result(
            relates_to="s3",
            result_name="s3_info",
            result_description="S3 Information",
            details=rego_ready_data,
            formatted="",
        )

        return item
