from pluggy import HookimplMarker
import yaml
from loguru import logger
from pydantic import BaseModel, Field
from typing import Annotated

from opsbox import Result

# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")

class RdsDownscalingConfig(BaseModel):
    rds_cpu_scaling_threshold: Annotated[int, Field(default = 20, description=r"% of cpu utilization under which an RDS instance is revommended to scale down. Default = 20.")]

class ScalingDown:
    """Plugin for identifying RDS instances that should be scaled down."""

    @hookimpl
    def grab_config(self) -> type[BaseModel]:
        """Return the plugin's configuration pydantic model.
        These should be things your plugin needs/wants to function.
        
        Returns:
            type[BaseModel]: The configuration model for the plugin."""
        return RdsDownscalingConfig

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
        data.details["input"]["rds_cpu_scaling_threshold"] = self.conf["rds_cpu_scaling_threshold"]
        return data

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
