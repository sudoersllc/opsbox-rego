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
            str: The formatted string containing the findings.
        """
        findings = data.details

        idle_instances = []
        if findings:
            idle = findings.get("underutilized_rds_instances", [])
            for instance in idle:
                idle_instances.append(f"Instance: {instance['InstanceIdentifier']} is idle.")
        try:
            idle_instances_yaml = yaml.dump(idle_instances, default_flow_style=False)
        except Exception as e:
            logger.error(f"Error formatting idle_instances details: {e}")
            idle_instances = ""

        template = """The following RDS storage instances are idle and can be downsized: \n 
        \n
        {idle_instances}
        \n """

        if findings:
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
