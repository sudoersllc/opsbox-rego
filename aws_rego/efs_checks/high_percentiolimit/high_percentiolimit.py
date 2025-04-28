from typing import Annotated
from pluggy import HookimplMarker
import yaml
from loguru import logger
from opsbox import Result
from pydantic import BaseModel, Field

# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")


class HighPercentIOLimitConfig(BaseModel):
    efs_percent_io_limit_threshold: Annotated[
        int,
        Field(
            default=60,
            description="Acceptable level of PercentIOLimit metric (0-100%).",
        ),
    ]


class HighPercentIOLimit:
    """Plugin for identifying EFSs with high percent IO limits."""

    @hookimpl
    def grab_config(self) -> type[BaseModel]:
        """Return the plugin's configuration pydantic model.
        These should be things your plugin needs/wants to function."""
        return HighPercentIOLimitConfig

    @hookimpl
    def set_data(self, model: type[BaseModel]) -> None:
        """Set the data for the plugin based on the model.

        Args:
            model (BaseModel): The model containing the data for the plugin."""
        self.conf = model.model_dump()

    def format_data(self, input: "Result") -> list:
        """Format the data for the plugin.

        Args:
            input (Result): The input data to format.

        Returns:
            list: The formatted data.
        """
        details = input.details["input"]
        logger.debug(f"Input details: {details}")

        # Initialize empty EFS list
        high_percent_io_limit_efs_set = []

        # Check if EFSs are present in the details
        efs_set = details.get("efss", [])

        # Find EFSs with high percent IO limits
        for efs in efs_set:
            if isinstance(efs, dict) and "PercentIOLimit" in efs:
                if efs["PercentIOLimit"] >= self.conf["efs_percent_io_limit_threshold"]:
                    high_percent_io_limit_efs_set.append(efs)

        return high_percent_io_limit_efs_set


    @hookimpl
    def report_findings(self, data: "Result"):
        """Report the findings of the plugin.
        Attributes:
            data (CheckResult): The result of the checks.
        Returns:
            str: The formatted string containing the findings.
        """
        findings = self.format_data(data)

        if findings:
            template = """The following EFSs have a high PercentIOLimit metric maximum value: \n{efs_set}"""
            try:
                efs_yaml = yaml.dump(
                    findings, default_flow_style=False
                )
            except Exception as e:
                logger.error(f"Error formatting EFS details: {e}")
                efs_yaml = "Error retrieving EFS details."

            formatted = template.format(efs_set=efs_yaml)

            return Result(
                relates_to="efs",
                result_name="high_percentiolimit",
                result_description="High PercentIOLimit EFSs",
                details=findings,
                formatted=formatted,
            )
        else:
            return Result(
                relates_to="efs",
                result_name="high_percentiolimit",
                result_description="High PercentIOLimit EFSs",
                details=findings,
                formatted="No EFSs with high percent IO limits found.",
            )

    @hookimpl
    def inject_data(self, data: "Result") -> "Result":
        """Inject data into the plugin.

        Args:
            data (Result): The data to inject into the plugin.

        Returns:
            Result: The data with the injected values.
        """
        data.details["input"]["efs_percent_io_limit_threshold"] = self.conf[
            "efs_percent_io_limit_threshold"
        ]
        return data
