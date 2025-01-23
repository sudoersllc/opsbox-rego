from pluggy import HookimplMarker
import yaml
from loguru import logger
from opsbox import Result

# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")


class EmptyStorage:
    """Plugin for identifying RDS storage instances with <40% storage utilization."""

    @hookimpl
    def report_findings(self, data: "Result"):
        """Report the findings of the plugin.
        Attributes:
            data (CheckResult): The result of the checks.
        Returns:
            Result: The formatted string containing the findings.
        """
        details = data.details

        storage_instances = []

        # Handle details as a list
        if isinstance(details, list):
            for instance in details:
                storage_instances.append(
                    f"Instance: {instance['InstanceIdentifier']} has {instance['StorageUtilization']}% storage utilization."
                )
        else:
            logger.error("Invalid details format: Expected a list.")
            return Result(
                relates_to="rds",
                result_name="empty_storage",
                result_description="RDS Storage Instances with <40% Storage Utilization",
                details=data.details,
                formatted="Error: Invalid data format for details.",
            )

        # Format the storage instances into YAML
        try:
            storage_instances_yaml = yaml.dump(storage_instances, default_flow_style=False)
        except Exception as e:
            logger.error(f"Error formatting storage_instances details: {e}")
            storage_instances_yaml = "Error formatting data."

        # Template for the output message
        template = """The following RDS storage instances are underutilized:

{storage_instances}
        """

        # Generate the result
        if storage_instances:
            return Result(
                relates_to="rds",
                result_name="empty_storage",
                result_description="RDS Storage Instances with <40% Storage Utilization",
                details=data.details,
                formatted=template.format(storage_instances=storage_instances_yaml),
            )
        else:
            return Result(
                relates_to="rds",
                result_name="empty_storage",
                result_description="RDS Storage Instances with <40% Storage Utilization",
                details=data.details,
                formatted="No RDS storage instances with <40% storage utilization found.",
            )
