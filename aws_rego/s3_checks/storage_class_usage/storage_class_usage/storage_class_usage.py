from pluggy import HookimplMarker
import yaml
from loguru import logger
from core.plugins import Result

# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")


class StorageClassUsage:
    """Plugin for identifying S3 buckets using GLACIER or STANDARD storage classes."""

    @hookimpl
    def report_findings(self, data: "Result"):
        """Report the findings of the plugin.
        Attributes:
            data (Result): The result of the checks.
        Returns:
            str: The formatted string containing the findings.
        """
        findings = data.details

        glacier_or_standard_ia_buckets = []
        if findings:
            buckets = findings.get("glacier_or_standard_ia_buckets", [])
            for bucket in buckets:
                if isinstance(bucket, dict) and "name" in bucket and "storage_class" in bucket:
                    bucket_obj = {bucket["name"]: {"storage_class": bucket["storage_class"]}}
                    glacier_or_standard_ia_buckets.append(bucket_obj)
                else:
                    logger.error(f"Unexpected format for bucket: {bucket}")
        try:
            buckets_yaml = yaml.dump(glacier_or_standard_ia_buckets, default_flow_style=False)
            # add the percentage of glacier or standard ia buckets to the output
        except Exception as e:
            logger.error(f"Error formatting bucket details: {e}")
            buckets_yaml = ""

        percentage_glacier_or_standard = findings.get("percentage_glacier_or_standard", 0)
        template = """The following S3 buckets are using GLACIER or STANDARD storage classes:
        \n
        {buckets}
        \n Percentage of buckets using GLACIER or STANDARD storage classes: {percentage_glacier_or_standard}% """

        if findings:
            return Result(
                relates_to="s3",
                result_name="storage_class_usage",
                result_description="S3 Buckets using GLACIER or STANDARD Storage Classes",
                details=data.details,
                formatted=template.format(
                    buckets=buckets_yaml, percentage_glacier_or_standard=percentage_glacier_or_standard
                ),
            )
        else:
            return Result(
                relates_to="s3",
                result_name="storage_class_usage",
                result_description="S3 Buckets using GLACIER or STANDARD Storage Classes",
                details=data.details,
                formatted="No S3 buckets using GLACIER or STANDARD storage classes found.",
            )
