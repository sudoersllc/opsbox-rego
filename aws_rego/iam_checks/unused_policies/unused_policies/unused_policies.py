from pluggy import HookimplMarker
import yaml
from loguru import logger
from opsbox import Result

# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")


class UnusedIAMPolicies:
    """Plugin for identifying IAM policies with zero attachments."""

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
