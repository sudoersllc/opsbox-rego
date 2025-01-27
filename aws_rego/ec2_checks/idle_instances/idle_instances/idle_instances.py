import yaml
from loguru import logger
from opsbox import Result
from pydantic import BaseModel, Field
from typing import Annotated
from datetime import datetime, timedelta
from pluggy import HookimplMarker

# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")


class EC2IdleInstancesConfig(BaseModel):
    ec2_cpu_idle_threshold: Annotated[
        int,
        Field(
            default=1,
            description="The % threshold for the average CPU utilization of an EC2 instance to be considered idle. Default is 1.",
        ),
    ]

class IdleInstances:
    """Plugin for identifying idle EC2 instances."""

    @hookimpl
    def grab_config(self) -> type[BaseModel]:
        """Return the plugin's configuration pydantic model.
        These should be things your plugin needs/wants to function."""
        return EC2IdleInstancesConfig

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
        data.details["input"]["ec2_cpu_idle_threshold"] = self.conf["ec2_cpu_idle_threshold"]
        return data

    @hookimpl
    def report_findings(self, data: Result) -> Result:
        """Report the findings of the plugin.
        Attributes:
            data (CheckResult): The result of the checks.
        Returns:
            str: The formatted string containing the findings.
        """
        findings = data.details
        logger.debug(f"Findings: {findings}")
        instances = []
        for instance in findings:
            instance_obj = {
                instance["instance_id"]: {
                    "region": instance["region"],
                    "state": instance["state"],
                    "avg_cpu_utilization": instance["avg_cpu_utilization"],
                    "instance_type": instance["instance_type"],
                    "operating_system": instance.get("operating_system", "N/A"),
                    "tags": instance.get("tags", {}),
                }
            }
            instances.append(instance_obj)
        try:
            instance_yaml = yaml.dump(instances, default_flow_style=False)
        except Exception as e:
            logger.error(f"Error formatting instance details: {e}")

        template = """The following EC2 instances are idle, with an average CPU utilization of less than 5%.
The data is presented in the following format:


{instances}"""

        if findings:
            formatted = template.format(instances=instance_yaml)
        else:
            formatted = "No idle EC2 instances found."

        item = Result(
            relates_to="ec2",
            result_name="idle_instances",
            result_description="Idle EC2 Instances",
            details=data.details,
            formatted=formatted,
        )
        return item
