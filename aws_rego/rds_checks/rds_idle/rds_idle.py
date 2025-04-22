from pluggy import HookimplMarker
import yaml
from loguru import logger
from opsbox import Result
from pydantic import BaseModel, Field
from typing import Annotated

# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")


class RdsIdleConfig(BaseModel):
    rds_cpu_idle_threshold: Annotated[
        int,
        Field(
            default=5,
            description=r"% of cpu utilization under which an RDS instance is flagged as idle. Default = 5.",
        ),
    ]


class RDSIdle:
    """Plugin for identifying idle RDS instances."""

    @hookimpl
    def grab_config(self) -> type[BaseModel]:
        """Return the plugin's configuration pydantic model.
        These should be things your plugin needs/wants to function.

        Returns:
            type[BaseModel]: The configuration model for the plugin."""
        return RdsIdleConfig

    @hookimpl
    def set_data(self, model: type[BaseModel]) -> None:
        """Set the data for the plugin based on the model.

        Args:
            model (BaseModel): The model containing the data for the plugin."""
        self.conf = model.model_dump()

    def format_data(self, input: "Result") -> dict:
        """Format the data for the plugin.

        Args:
            input (Result): The input data to format.

        Returns:
            dict: The formatted data.
        """
        details = input.details["input"]

        idle_instances = [instance for instance in details["rds_instances"] if instance.CPUUtilization < self.conf["rds_cpu_idle_threshold"]]

        return idle_instances

    @hookimpl
    def report_findings(self, data: "Result"):
        """Report the findings of the plugin.
        Attributes:
            data (Result): The result of the checks.
        Returns:
            Result: The formatted string containing the findings.
        """
        findings = self.format_data(data)

        idle_instances = []

        # Handle findings as a list
        if isinstance(findings, list):
            for instance in findings:
                if (
                    instance.get("CPUUtilization", 0) < self.conf["rds_cpu_idle_threshold"]
                ):  # Check if the instance is idle
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
                details=findings,
                formatted=template.format(idle_instances=idle_instances_yaml),
            )
        else:
            return Result(
                relates_to="rds",
                result_name="idle_instances",
                result_description="Idle RDS Instances",
                details=findings,
                formatted="No idle RDS instances found.",
            )
