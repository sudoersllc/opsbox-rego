from pluggy import HookimplMarker
import yaml
from loguru import logger
from core.plugins import Result
from pydantic import BaseModel, Field
from typing import Annotated

# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")


class UnusedPoliciesConfig(BaseModel):
    iam_unused_attachment_threshold: Annotated[
        int,
        Field(
            default=0,
            description="The number of attachments a policy must have to be considered used. Default is 0.",
        ),
    ]

class UnusedIAMPolicies:
    """Plugin for identifying IAM policies with zero attachments."""

    @hookimpl
    def grab_config(self) -> type[BaseModel]:
        """Return the plugin's configuration pydantic model.
        These should be things your plugin needs/wants to function."""
        return UnusedPoliciesConfig

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
        data.details["input"]["iam_unused_attachment_threshold"] = self.conf["iam_unused_attachment_threshold"]
        return data

    @hookimpl
    def report_findings(self, data: "Result"):
        """Report the findings of the plugin.
        Attributes:
            data (CheckResult): The result of the checks.
        Returns:
            Result: The formatted result object containing the findings.
        """
        details = data.details

        # Handle cases where details is a list or dictionary
        if isinstance(details, list):
            # Assume details directly contains unused policies
            unused_policies = details
        elif isinstance(details, dict):
            # Extract unused policies from the dictionary
            unused_policies = details.get("policy", [])
        else:
            logger.error("Invalid details format: Expected a dictionary or list.")
            return Result(
                relates_to="iam",
                result_name="iam_unused_policies",
                result_description="IAM Policies with Zero Attachments",
                details=data.details,
                formatted="Error: Invalid data format for details.",
            )

        # Format the unused policies list into YAML
        try:
            unused_policies_yaml = yaml.dump(unused_policies, default_flow_style=False)
        except Exception as e:
            logger.error(f"Error formatting unused IAM policies: {e}")
            unused_policies_yaml = "Error formatting data."

        # Template for the output message
        if unused_policies:
            formatted_output = f"""The following IAM policies have zero attachments:

{unused_policies_yaml}
            """
            logger.info(f"Found {len(unused_policies)} unused IAM policies.")
        else:
            formatted_output = "No unused IAM policies found."
            logger.info("No unused IAM policies found.")

        # Generate the result with formatted output
        return Result(
            relates_to="iam",
            result_name="iam_unused_policies",
            result_description="IAM Policies with Zero Attachments",
            details=data.details,
            formatted=formatted_output,
        )
