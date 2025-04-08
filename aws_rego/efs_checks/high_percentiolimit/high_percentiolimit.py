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

    @hookimpl
    def report_findings(self, data: "Result"):
        """Report the findings of the plugin.
        Attributes:
            data (CheckResult): The result of the checks.
        Returns:
            str: The formatted string containing the findings.
        """
        findings = data.details

        high_percent_io_limit_efs_set = []
        if findings:
            if findings is type(dict):
                efs_set = findings.get("high_percent_io_limit_efs_set", [])
            else:
                efs_set = findings
            for efs in efs_set:
                if (
                    isinstance(efs, dict)
                    and "Name" in efs
                    and "Id" in efs
                    and "PercentIOLimit" in efs
                ):
                    high_percent_io_limit_efs_set.append(
                        {
                            efs["Id"]: {
                                "Id": efs["Id"],
                                "Name": efs["Name"],
                                "PercentIOLimit": efs["PercentIOLimit"],
                            }
                        }
                    )
                else:
                    logger.error(f"Invalid EFS data: {efs}")

            template = """The following EFSs have a high PercentIOLimit metric maximum value: \n{efs_set}"""
            try:
                efs_yaml = yaml.dump(
                    high_percent_io_limit_efs_set, default_flow_style=False
                )
            except Exception as e:
                logger.error(f"Error formatting EFS details: {e}")
                efs_yaml = "Error retrieving EFS details."

            formatted = template.format(efs_set=efs_yaml)

            return Result(
                relates_to="efs",
                result_name="high_percentiolimit",
                result_description="High PercentIOLimit EFSs",
                details=data.details,
                formatted=formatted,
            )
        else:
            return Result(
                relates_to="efs",
                result_name="high_percentiolimit",
                result_description="High PercentIOLimit EFSs",
                details=data.details,
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
