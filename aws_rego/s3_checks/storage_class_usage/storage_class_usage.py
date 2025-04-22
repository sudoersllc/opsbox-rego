from pluggy import HookimplMarker
import yaml
from loguru import logger
from opsbox import Result
from pydantic import BaseModel, Field
from typing import Annotated
from datetime import datetime, timedelta


# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")


class StorageClassUsageConfig(BaseModel):
    s3_stale_bucket_date_threshold: Annotated[
        datetime,
        Field(
            default=(datetime.now() - timedelta(days=90)),
            description="How long ago a bucket has to have been last used for it to be considered stale. Default is 90 days.",
        ),
    ]


class StorageClassUsage:
    """Plugin for analyzing S3 bucket storage classes, stale buckets, and mixed storage."""

    @hookimpl
    def grab_config(self) -> type[BaseModel]:
        """Return the plugin's configuration pydantic model.
        These should be things your plugin needs/wants to function."""
        return StorageClassUsageConfig

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
        timestamp = int(self.conf["s3_stale_bucket_date_threshold"].timestamp())
        data.details["input"]["s3_stale_bucket_date_threshold"] = timestamp
        return data
    
    def format_data(self, input: "Result") -> dict:
        """
        Analyzes S3 bucket storage classes and applies policy checks.
        
        Args:
            details (dict): The Result object's details dictionary containing bucket information
        
        Returns:
            dict: Analysis results with counts, percentages, bucket lists, and compliance status
        """
        details = input.details["input"]
        buckets = details.get('buckets', [])
        stale_threshold = self.conf["s3_stale_bucket_date_threshold"].timestamp()
        
        # Initialize bucket lists by category
        glacier_or_standard_ia_buckets = []
        stale_buckets = []
        mixed_storage_buckets = []
        
        # Analyze each bucket
        for bucket in buckets:
            # Check for GLACIER or STANDARD_IA storage
            if bucket.get('storage_class') == 'GLACIER' or bucket.get('storage_class') == 'STANDARD_IA':
                glacier_or_standard_ia_buckets.append(bucket)
            
            # Check for stale buckets
            if bucket.get('last_modified') and bucket.get('last_modified') < stale_threshold:
                stale_buckets.append(bucket)
            
            # Check for MIXED storage
            if bucket.get('storage_class') == 'MIXED':
                mixed_storage_buckets.append(bucket)
        
        # Calculate counts
        count_glacier_or_standard_ia = len(glacier_or_standard_ia_buckets)
        count_stale = len(stale_buckets)
        count_mixed = len(mixed_storage_buckets)
        total_buckets = len(buckets)
        
        # Calculate percentages
        percentage_glacier_or_standard_ia = (100 * count_glacier_or_standard_ia / total_buckets) if total_buckets > 0 else 0
        percentage_stale = (100 * count_stale / total_buckets) if total_buckets > 0 else 0
        percentage_mixed = (100 * count_mixed / total_buckets) if total_buckets > 0 else 0
        
        # Apply policy checks
        allow_glacier_or_standard_ia = percentage_glacier_or_standard_ia >= 70
        flag_stale_buckets = percentage_stale > 20
        allow_no_mixed_storage = count_mixed == 0
        
        # Build result dictionary
        analysis_results = {
            "total_buckets": total_buckets,
            "count_glacier_or_standard_ia": count_glacier_or_standard_ia,
            "count_stale": count_stale,
            "count_mixed": count_mixed,
            "percentage_glacier_or_standard_ia": percentage_glacier_or_standard_ia,
            "percentage_stale": percentage_stale,
            "percentage_mixed": percentage_mixed,
            "stale_buckets": stale_buckets,
            "mixed_storage_buckets": mixed_storage_buckets,
            "glacier_or_standard_ia_buckets": glacier_or_standard_ia_buckets,
            "policy_checks": {
                "allow_glacier_or_standard_ia": allow_glacier_or_standard_ia,
                "flag_stale_buckets": flag_stale_buckets,
                "allow_no_mixed_storage": allow_no_mixed_storage
            }
        }
        
        return analysis_results

    @hookimpl
    def report_findings(self, data: "Result"):
        """Report the findings of the plugin.

        Attributes:
            data (Result): The result of the checks.

        Returns:
            Result: The result object with formatted findings.
        """
        findings = self.format_data(data)

        # Initialize variables for storing different categories of buckets
        glacier_or_standard_ia_buckets = []
        stale_buckets = []
        mixed_storage_buckets = []

        if findings:
            # Parse buckets for each category
            glacier_or_standard_ia_buckets = findings.get(
                "glacier_or_standard_ia_buckets", []
            )
            stale_buckets = findings.get("stale_buckets", [])
            mixed_storage_buckets = findings.get("mixed_storage_buckets", [])

            # Format buckets into YAML
            def format_buckets(bucket_list, description):
                try:
                    return f"{description}:\n{yaml.dump(bucket_list, default_flow_style=False)}"
                except Exception as e:
                    logger.error(f"Error formatting {description}: {e}")
                    return f"{description}:\nError formatting details.\n"

            glacier_or_standard_ia_output = format_buckets(
                glacier_or_standard_ia_buckets, "GLACIER or STANDARD_IA Buckets"
            )
            stale_buckets_output = format_buckets(stale_buckets, "Stale Buckets")
            mixed_storage_output = format_buckets(
                mixed_storage_buckets, "MIXED Storage Buckets"
            )

            # Collect percentages
            percentage_glacier_or_standard_ia = findings.get(
                "percentage_glacier_or_standard_ia", 0
            )
            percentage_stale = findings.get("percentage_stale", 0)
            percentage_mixed = findings.get("percentage_mixed", 0)

            # Template for formatted result
            template = """The following S3 bucket analysis was performed:
{glacier_or_standard_ia}
{stale_buckets}
{mixed_storage}

    Summary:
    - Percentage of GLACIER or STANDARD_IA buckets: {percentage_glacier_or_standard_ia}%
    - Percentage of stale buckets: {percentage_stale}%
    - Percentage of MIXED storage buckets: {percentage_mixed}%
    """

            # Generate the formatted result
            formatted_output = template.format(
                glacier_or_standard_ia=glacier_or_standard_ia_output,
                stale_buckets=stale_buckets_output,
                mixed_storage=mixed_storage_output,
                percentage_glacier_or_standard_ia=percentage_glacier_or_standard_ia,
                percentage_stale=percentage_stale,
                percentage_mixed=percentage_mixed,
            )

            # Determine result description based on findings
            result_description = "S3 Bucket Analysis including GLACIER/IA usage, stale buckets, and mixed storage."

            # Return the result
            return Result(
                relates_to="s3",
                result_name="bucket_analysis",
                result_description=result_description,
                details=findings,
                formatted=formatted_output,
            )
        else:
            return Result(
                relates_to="s3",
                result_name="bucket_analysis",
                result_description="S3 Bucket Analysis",
                details=findings,
                formatted="No S3 bucket analysis performed.",
            )
