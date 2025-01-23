from pluggy import HookimplMarker
import yaml
from loguru import logger

from opsbox import Result

# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")


class ScalingDown:
    """Plugin for identifying RDS instances that should be scaled down."""

    @hookimpl
    def report_findings(self, data: "Result"):
        """Report the findings of the plugin."""

        findings = data.details

        scaling_instances = []
        if findings:
            scaling = findings.get("recommendations_for_scaling_down", [])
            for instance in scaling:
                scaling_instances.append(f"Instance: {instance['InstanceIdentifier']} should be scaled down.")
        try:
            scaling_instances_yaml = yaml.dump(scaling_instances, default_flow_style=False)
        # add the percentage of glacier or standard ia buckets to the output
        except Exception as e:
            logger.error(f"Error formatting scaling_instances details: {e}")
            scaling_instances = ""

        template = """The following RSD storage instances should be scaled down:
        
{scaling_instances}"""

        if findings:
            return Result(
                relates_to="rds",
                result_name="scaling_down",
                result_description="RDS Instances that should be scaled down",
                details=data.details,
                formatted=template.format(scaling_instances=scaling_instances_yaml),
            )
        else:
            return Result(
                relates_to="rds",
                result_name="scaling_down",
                result_description="RDS Instances that should be scaled down",
                details=data.details,
                formatted="No RDS instances that should be scaled down found.",
            )
