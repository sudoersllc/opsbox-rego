from pluggy import HookimplMarker
import yaml
from loguru import logger
from core.plugins import Result

# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")


class RDSIdle:
    """Plugin for identifying idle RDS instances."""

    @hookimpl
    def report_findings(self, data: "Result"):
        """Report the findings of the plugin.
        Attributes:
            data (Result): The result of the checks.
        Returns:
            Result: The formatted string containing the findings.
        """
        findings = data.details

        idle_instances = []

        # Handle findings as a list
        if isinstance(findings, list):
            for instance in findings:
                if instance.get("CPUUtilization", 0) < 5:  # Check if the instance is idle
                    idle_instances.append(
                        f"Instance: {instance['InstanceIdentifier']} is idle."
                    )
        else:
            logger.error("Invalid findings format: Expected a list.")
            return Result(
                relates_to="rds",
                result_name="idle_instances",
                result_description="Idle RDS Instances",
                details=data.details,
                formatted="Error: Invalid data format for findings.",
            )

        # Format the idle instances into YAML
        try:
            idle_instances_yaml = yaml.dump(idle_instances, default_flow_style=False)
        except Exception as e:
            logger.error(f"Error formatting idle_instances details: {e}")
            idle_instances_yaml = "Error formatting data."

        # Template for the output message
        template = """The following RDS storage instances are idle and can be downsized:

{idle_instances}
        """

        # Generate the result
        if idle_instances:
            return Result(
                relates_to="rds",
                result_name="idle_instances",
                result_description="Idle RDS Instances",
                details=data.details,
                formatted=template.format(idle_instances=idle_instances_yaml),
            )
        else:
            return Result(
                relates_to="rds",
                result_name="idle_instances",
                result_description="Idle RDS Instances",
                details=data.details,
                formatted="No idle RDS instances found.",
            )
