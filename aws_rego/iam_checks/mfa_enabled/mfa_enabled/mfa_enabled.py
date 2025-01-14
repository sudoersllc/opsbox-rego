from pluggy import HookimplMarker
import yaml
from loguru import logger
from core.plugins import Result

# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")


class IAMMFADisabled:
    """Plugin for identifying IAM users without MFA enabled."""

    @hookimpl
    def report_findings(self, data: "Result"):
        """Report the findings of the plugin.
        Attributes:
            data (CheckResult): The result of the checks.
        Returns:
            Result: The formatted result object containing the findings.
        """
        details = data.details

        # Handle details as a list or dictionary
        if isinstance(details, list):
            # If details is a list, assume it directly contains the users
            unused_policies = details
        elif isinstance(details, dict):
            # If details is a dictionary, get the specific key
            unused_policies = details.get("users_without_mfa", [])
        else:
            logger.error("Invalid details format: Expected a dictionary or list.")
            return Result(
                relates_to="iam",
                result_name="users_without_mfa",
                result_description="IAM Users without MFA",
                details=data.details,
                formatted="Error: Invalid data format for details.",
            )

        # Format the list into YAML
        try:
            unused_policies_yaml = yaml.dump(unused_policies, default_flow_style=False)
        except Exception as e:
            logger.error(f"Error formatting users without MFA: {e}")
            unused_policies_yaml = "Error formatting data."

        # Template for the output message
        if unused_policies:
            formatted_output = f"""The following IAM users do not have MFA enabled:

{unused_policies_yaml}
            """
            logger.info(f"Found {len(unused_policies)} IAM users without MFA.")
        else:
            formatted_output = "No IAM users found without MFA."
            logger.info("No IAM users without MFA found.")

        # Generate the result
        return Result(
            relates_to="iam",
            result_name="users_without_mfa",
            result_description="IAM Users without MFA",
            details=data.details,
            formatted=formatted_output,
        )
