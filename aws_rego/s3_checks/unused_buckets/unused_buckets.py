from pluggy import HookimplMarker
import yaml
from loguru import logger
from datetime import datetime
from core.plugins import Result


# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")


class UnusedBuckets:
    """Plugin for identifying unused S3 buckets."""

    def report_findings(self, data: "Result"):
        """Format the check results in a LLM-readable format."""
        findings = data.details

        old_buckets = []
        if findings:
            buckets = findings.get("unused_buckets", [])
            for bucket in buckets:
                if isinstance(bucket, dict) and "name" in bucket and "last_modified" in bucket:
                    last_modified = datetime.fromtimestamp(bucket["last_modified"]).strftime("%Y-%m-%d %H:%M:%S")
                    bucket_obj = {bucket["name"]: {"last_modified": last_modified}}
                    old_buckets.append(bucket_obj)
                else:
                    logger.error(f"Unexpected format for bucket: {bucket}")
        try:
            buckets_yaml = yaml.dump(old_buckets, default_flow_style=False)
        except Exception as e:
            logger.error(f"Error formatting bucket details: {e}")
            buckets_yaml = ""

        template = """The following S3 buckets havent been used:
        {buckets}
        """

        if findings:
            return Result(
                relates_to="s3",
                result_name="unused_buckets",
                result_description="Unused S3 Buckets",
                details=data.details,
                formatted=template.format(buckets=buckets_yaml),
            )
        else:
            return Result(
                relates_to="s3",
                result_name="unused_buckets",
                result_description="Unused S3 Buckets",
                details=data.details,
                formatted="No unused S3 buckets found.",
            )
