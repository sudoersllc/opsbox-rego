from pluggy import HookimplMarker
import yaml
from loguru import logger
from opsbox import Result
from pydantic import BaseModel, Field
from typing import Annotated
from datetime import datetime, timedelta

# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")


class OverdueAPIKeysConfig(BaseModel):
    iam_overdue_key_date_threshold: Annotated[
        datetime,
        Field(
            default=(datetime.now() - timedelta(days=90)),
            description="How long ago a key was last used for it to be considered overdue. Default is 90 days.",
        ),
    ]


class OverdueAPIKeysIAM:
    """Plugin for identifying IAM keys that are overdue for rotation."""

    @hookimpl
    def grab_config(self) -> type[BaseModel]:
        """Return the plugin's configuration pydantic model.
        These should be things your plugin needs/wants to function."""
        return OverdueAPIKeysConfig

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
        timestamp = int(self.conf["iam_overdue_key_date_threshold"].timestamp() * 1e9)
        data.details["input"]["iam_overdue_key_date_threshold"] = timestamp
        return data

    def report_findings(self, data: "Result"):
        """Report the findings of the plugin.
        Attributes:
            data (CheckResult): The result of the checks.
        Returns:
            str: The formatted string containing the findings.
        """
        details = data.details

        # Directly get unused policies from the Rego result
        unused_policies = details.get("overdue_api_keys", [])

        # Format the unused policies list into YAML for better readability
        try:
            unused_policies_yaml = yaml.dump(unused_policies, default_flow_style=False)
        except Exception as e:
            logger.error(f"Error formatting overdue API keys: {e}")
            unused_policies_yaml = ""

        # Template for the output message
        template = """The following IAM API keys are overdue:
        
{unused_policies}"""
        logger.info(unused_policies_yaml)

        # Generate the result with formatted output
        if unused_policies:
            return Result(
                relates_to="iam",
                result_name="overdue_api_keys",
                result_description="IAM API Keys Overdue",
                details=data.details,
                formatted=template.format(unused_policies=unused_policies_yaml),
            )
        else:
            return Result(
                relates_to="iam",
                result_name="overdue_api_keys",
                result_description="IAM API Keys Overdue",
                details=data.details,
                formatted="No overdue API keys found.",
            )
