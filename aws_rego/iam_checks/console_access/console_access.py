from pluggy import HookimplMarker
import yaml
from loguru import logger
from core.plugins import Result

# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")


class ConsoleAccessIAM:
    """Plugin for identifying IAM policies with zero attachments."""

    def report_findings(self, data: "Result"):
        """Report the findings of the plugin.
        Attributes:
            data (CheckResult): The result of the checks.
        Returns:
            str: The formatted string containing the findings.
        """
        details = data.details


        # Directly get unused policies from the Rego result
        unused_policies = details.get("users_with_console_access", [])
        
        # Format the unused policies list into YAML for better readability
        try:
            unused_policies_yaml = yaml.dump(unused_policies, default_flow_style=False)
        except Exception as e:
            logger.error(f"Error formatting users with console access: {e}")
            unused_policies_yaml = ""

        # Template for the output message
        template = """The following IAM users have console access:
        
        {unused_policies}
        """
        logger.info(unused_policies_yaml)
        
        # Generate the result with formatted output
        if unused_policies:
            return Result(
                relates_to="iam",
                result_name="users_without_mfa",
                result_description="IAM Users with Console Access",
                details=data.details,
                formatted=template.format(unused_policies=unused_policies_yaml),
            )
        else:
            return Result(
                relates_to="iam",
                result_name="users_without_mfa",
                result_description="IAM Users with Console Access",
                details=data.details,
                formatted="No IAM users found with console access.",
            )
