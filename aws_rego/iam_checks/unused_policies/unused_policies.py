from pluggy import HookimplMarker
import yaml
from loguru import logger
from opsbox import Result
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
    
    def format_result(self, input: "Result") -> list:
        """Format the result for the plugin.
        Args:
            input (Result): The input data to format.
        Returns:
            list: The formatted data.
        """
        details = input.details["input"]

        unused_policies = []

        for policy in details["iam_policies"]:
            if policy.get("attachment_count") < self.conf["iam_unused_attachment_threshold"]:
                unused_policies.append(policy)

        return unused_policies

    @hookimpl
    def report_findings(self, data: "Result"):
        """Report the findings of the plugin.
        Attributes:
            data (CheckResult): The result of the checks.
        Returns:
            Result: The formatted result object containing the findings.
        """
        details = self.format_result(data)

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
                details=details,
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
            details=details,
            formatted=formatted_output,
        )
