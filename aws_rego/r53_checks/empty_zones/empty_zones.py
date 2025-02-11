from pluggy import HookimplMarker
import yaml
from loguru import logger
from opsbox import Result

# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")


class EmptyZones:
    """Plugin for identifying Route 53 hosted zones with no DNS records."""

    def report_findings(self, data: "Result"):
        """Report the findings of the plugin.
        Attributes:
            data (CheckResult): The result of the checks.
        Returns:
            str: The formatted string containing the findings.
        """
        details = data.details
        logger.info(f"Details: {details}")

        # Directly get empty hosted zones from the Rego result
        empty_zones = details.get("empty_hosted_zones", [])

        # Format the empty zones list into YAML for better readability
        try:
            empty_zones_yaml = yaml.dump(empty_zones, default_flow_style=False)
        except Exception as e:
            logger.error(f"Error formatting empty hosted zones: {e}")
            empty_zones_yaml = ""

        # Template for the output message
        template = """The following Route 53 hosted zones have no DNS records:
        
{empty_zones}"""
        logger.info(empty_zones_yaml)

        # Generate the result with formatted output
        if empty_zones:
            return Result(
                relates_to="r53",
                result_name="route53_empty_zones",
                result_description="Route 53 Hosted Zones with No Records",
                details=data.details,
                formatted=template.format(empty_zones=empty_zones_yaml),
            )
        else:
            return Result(
                relates_to="r53",
                result_name="route53_empty_zones",
                result_description="Route 53 Hosted Zones with No Records",
                details=data.details,
                formatted="No empty Route 53 hosted zones found.",
            )
