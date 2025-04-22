from pluggy import HookimplMarker
import yaml
from loguru import logger
from opsbox import Result
from pydantic import BaseModel, Field
from typing import Annotated
from datetime import datetime, timedelta

# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")


class UnusedBucketsConfig(BaseModel):
    s3_unused_bucket_date_threshold: Annotated[
        datetime,
        Field(
            default=(datetime.now() - timedelta(days=90)),
            description="How long ago a bucket has to have been last used for it to be considered unused. Default is 90 days.",
        ),
    ]


class UnusedBuckets:
    """Plugin for identifying unused S3 buckets."""

    @hookimpl
    def grab_config(self) -> type[BaseModel]:
        """Return the plugin's configuration pydantic model.
        These should be things your plugin needs/wants to function."""
        return UnusedBucketsConfig

    @hookimpl
    def set_data(self, model: type[BaseModel]) -> None:
        """Set the data for the plugin based on the model.

        Args:
            model (BaseModel): The model containing the data for the plugin."""
        self.conf = model.model_dump()

    @hookimpl
    def inject_data(self, data: "Result") -> "Result":
        """Inject data into the plugin.

        Args:
            data (Result): The data to inject into the plugin.

        Returns:
            Result: The data with the injected values.
        """
        timestamp = int(self.conf["s3_unused_bucket_date_threshold"].timestamp())
        data.details["input"]["s3_unused_bucket_date_threshold"] = timestamp
        return data
    
    def format_data(self, input: "Result") -> dict:
        """Format the data for the plugin.

        Args:
            input (Result): The input data to format.

        Returns:
            dict: The formatted data.
        """
        # Format the data as needed
        details = input.details["input"]
        buckets = [bucket for bucket in details["buckets"] if bucket["last_modified"] is not None]
        buckets = [x for x in buckets if x["last_modified"] < self.conf["s3_unused_bucket_date_threshold"].timestamp()]
        return buckets

    @hookimpl
    def report_findings(self, data: "Result"):
        """Format the check results in a readable format."""
        findings = self.format_data(data)

        old_buckets = []
        if findings:
            buckets = findings
            for bucket in buckets:
                if (
                    isinstance(bucket, dict)
                    and "name" in bucket
                    and "last_modified" in bucket
                ):
                    try:
                        # Convert timestamp to human-readable date format
                        last_modified = datetime.fromtimestamp(
                            bucket["last_modified"]
                        ).strftime("%Y-%m-%d %H:%M:%S")
                        bucket_obj = {
                            bucket["name"]: {
                                "last_modified": last_modified,
                                "storage_class": bucket.get("storage_class", "Unknown"),
                            }
                        }
                        old_buckets.append(bucket_obj)
                    except Exception as e:
                        logger.error(
                            f"Error formatting bucket's last_modified date: {e}"
                        )
                else:
                    logger.error(f"Unexpected format for bucket: {bucket}")
            try:
                buckets_yaml = yaml.dump(old_buckets, default_flow_style=False)
            except Exception as e:
                logger.error(f"Error formatting bucket details: {e}")
                buckets_yaml = ""

            template = """The following S3 buckets have not been used:
{buckets}"""
            return Result(
                relates_to="s3",
                result_name="unused_buckets",
                result_description="Unused S3 Buckets",
                details=findings,
                formatted=template.format(buckets=buckets_yaml),
            )
        else:
            return Result(
                relates_to="s3",
                result_name="unused_buckets",
                result_description="Unused S3 Buckets",
                details=findings,
                formatted="No unused S3 buckets found.",
            )
