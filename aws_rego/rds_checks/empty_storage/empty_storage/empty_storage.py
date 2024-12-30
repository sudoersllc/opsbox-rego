from pluggy import HookimplMarker
import yaml
from loguru import logger
from core.plugins import Result

# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")


class EmptyStorage:
    """Plugin for identifying RDS storage instances with <40% storage utilization."""

    def report_findings(self, data: "Result"):
        """Report the findings of the plugin.
        Attributes:
            data (CheckResult): The result of the checks.
        Returns:
            str: The formatted string containing the findings.
        """
        details = data.details

        storage_instances = []
        if details:
            storage = details.get("empty_storage_instances", [])
            for instance in storage:
                storage_instances.append(
                    f"Instance: {instance['InstanceIdentifier']} has {instance['StorageUtilization']}% storage utilization."  # noqa: E501
                )
        try:
            storage_instances_yaml = yaml.dump(storage_instances, default_flow_style=False)
        # add the percentage of glacier or standard ia buckets to the output
        except Exception as e:
            logger.error(f"Error formatting storage_instances details: {e}")
            storage_instances = ""

        template = """The following RSD storage instances are underutilized:
        \n
        {storage_instances}
        \n """

        if details:
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
