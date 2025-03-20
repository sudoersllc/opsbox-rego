from pluggy import HookimplMarker
import yaml
from loguru import logger
from opsbox import Result
from pydantic import BaseModel, Field
from typing import Annotated

# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")


class EmptyStorageConfig(BaseModel):
    rds_empty_storage_threshold: Annotated[
        int,
        Field(
            default=40,
            description=r"% of storage utilization under which an RDS instance is flagged as empty. Default = 40.",
        ),
    ]


class EmptyStorage:
    """Plugin for identifying RDS storage instances with low storage utilization."""

    @hookimpl
    def grab_config(self) -> type[BaseModel]:
        """Return the plugin's configuration pydantic model.
        These should be things your plugin needs/wants to function.

        Returns:
            type[BaseModel]: The configuration model for the plugin."""
        return EmptyStorageConfig

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
        data.details["input"]["rds_empty_storage_threshold"] = self.conf[
            "rds_empty_storage_threshold"
        ]
        return data

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
            storage_instances_yaml = yaml.dump(
                storage_instances, default_flow_style=False
            )
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
