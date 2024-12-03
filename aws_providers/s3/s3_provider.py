from pluggy import HookimplMarker
from pydantic import BaseModel, Field
from datetime import datetime
import boto3
from loguru import logger
import threading
from core.plugins import Result
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

            aws_access_key_id: Annotated[str,Field(..., description="AWS access key ID", required=True)]
            aws_secret_access_key: Annotated[str,Field(..., description="AWS secret access key", required=True)]
            aws_region: Annotated[
                str | None, Field(description="AWS-Region", required=False, default=None)
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

    def gather_data(self):
        """Gather data related to AWS S3 (buckets, objects, and storage classes).
        Attributes:
            credentials: dict: AWS credentials
        Returns:
            dict: A dictionary containing the gathered data
                "input": {
                    "objects": list: List of objects in the S3 buckets
                    "buckets": list: List of S3 buckets
                    "current_time": int: The current time in seconds since the epoch
                }
        """
        logger.info("Gathering data for S3 plugin...")

        all_buckets = []  # List to store bucket details
        all_objects = []  # List to store object details
        object_count_threshold = 30  # Threshold for object count per bucket
        bucket_count_threshold = 100  # Threshold for bucket count
        processed_buckets = 0  # Counter for processed buckets
        credentials = self.credentials

        logger.info(credentials["aws_region"])

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

        region_threads = []  # List to store threads
        def process_region(region):

            s3_client = boto3.client(
                "s3",
                aws_access_key_id=self.credentials["aws_access_key_id"],
                aws_secret_access_key=self.credentials["aws_secret_access_key"],
                region_name=region,
            )

            response = s3_client.list_buckets()  # List all buckets
            logger.trace(f"List of buckets: {response}")
            buckets = response["Buckets"]  # Extract buckets from the response
            threads = []  # List to store threads

            def process_bucket(bucket):
                nonlocal processed_buckets  # Access the nonlocal variable processed_buckets
                bucket_name = bucket["Name"]

                bucket_details = {
                    "BucketName": bucket_name,
                    "CreationDate": bucket["CreationDate"].isoformat(),
                    "LastModified": None,
                }

                all_buckets.append(bucket_details)
                most_recent_last_modified = None
                processed_buckets += 1
                try:
                    paginator = s3_client.get_paginator("list_objects_v2")  # Paginate through bucket objects
                    bucket_storage_classes = set()
                    object_counter = 0
                    for page in paginator.paginate(Bucket=bucket_name):
                        for obj in page.get("Contents", []):
                            if object_counter >= object_count_threshold:
                                logger.warning(
                                    f"Reached object count threshold for bucket {bucket_name}, skipping remaining objects"
                                )
                                break
                            # Extract object details
                            object_details = {
                                "Key": obj["Key"],
                                "LastModified": obj["LastModified"].timestamp(),
                                "StorageClass": obj.get("StorageClass", "STANDARD"),  
                                # Default to STANDARD if not provided
                            }
                            bucket_storage_classes.add(object_details["StorageClass"])
                            # Update the most recent last modified date
                            if most_recent_last_modified is None or obj["LastModified"] > most_recent_last_modified:
                                most_recent_last_modified = obj["LastModified"]
                                bucket_details["LastModified"] = obj["LastModified"].timestamp()
                            logger.debug(
                                f"Added object {obj['Key']} with storage class {object_details['StorageClass']} to data, last modified: {obj['LastModified']}"  # noqa: E501
                            )
                            all_objects.append(object_details)
                            object_counter += 1

                        if object_counter >= object_count_threshold:
                            break

                    # If bucket has mixed storage classes, you can decide on a policy (e.g., prioritize non-standard classes)  # noqa: E501
                    inferred_storage_class = (
                        bucket_storage_classes.pop() if len(bucket_storage_classes) == 1 else "MIXED"
                    )
                    for bucket in all_buckets:
                        if bucket["BucketName"] == bucket_name:
                            bucket["StorageClass"] = inferred_storage_class
                    if processed_buckets >= bucket_count_threshold:
                        logger.warning("Reached bucket count threshold, skipping remaining buckets")
                        return

                except Exception as e:
                    logger.error(f"Error listing objects for bucket {bucket_name}: {e}")

            # Process the buckets in parallel
            for bucket in buckets:
                if processed_buckets >= bucket_count_threshold:
                    break
                thread = threading.Thread(target=process_bucket, args=(bucket,))
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

        
        
        for region in regions:
            region_thread = threading.Thread(target=process_region, args=(region,))
            region_threads.append(region_thread)
            region_thread.start()

        # Wait for all threads to complete
        for region_thread in region_threads:
            region_thread.join()

        # Prepare the data in a format that can be consumed by Rego
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
