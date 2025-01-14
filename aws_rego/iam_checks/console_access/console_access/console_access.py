from pluggy import HookimplMarker
import yaml
from loguru import logger
from core.plugins import Result

# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")


class ConsoleAccessIAM:
    """Plugin for identifying IAM users with console access."""

    @hookimpl
    def report_findings(self, data: "Result"):
        """Report the findings of the plugin.
        Attributes:
            data (CheckResult): The result of the checks.
        Returns:
            Result: The formatted result object containing the findings.
        """
        details = data.details

        # Check if details is a list
        if isinstance(details, list):
            # Assume details is a list of IAM users
            unused_policies = details
        elif isinstance(details, dict):
            # Extract users with console access from the dictionary
            unused_policies = details.get("users_with_console_access", [])
        else:
            logger.error("Invalid details format: Expected a dictionary or list.")
            return Result(
                relates_to="iam",
                result_name="users_with_console_access",
                result_description="IAM Users with Console Access",
                details=data.details,
                formatted="Error: Invalid data format for details.",
            )

        try:
            # Format the users with console access list into YAML for better readability
            unused_policies_yaml = yaml.dump(unused_policies, default_flow_style=False)
        except Exception as e:
            logger.error(f"Error formatting users with console access: {e}")
            unused_policies_yaml = "Error formatting data."

        # Template for the output message
        if unused_policies:
            formatted_output = f"""The following IAM users have console access:
            
{unused_policies_yaml}
            """
            logger.info(f"Found {len(unused_policies)} users with console access.")
        else:
            formatted_output = "No IAM users found with console access."
            logger.info("No IAM users with console access found.")

        # Generate the result with formatted output
        return Result(
            relates_to="iam",
            result_name="users_with_console_access",
            result_description="IAM Users with Console Access",
            details=data.details,
            formatted=formatted_output,
        )
