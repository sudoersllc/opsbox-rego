from pluggy import HookimplMarker
import yaml
from loguru import logger
from opsbox import Result
from pprint import pprint

# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")


class EmptyZones:
    """Plugin for identifying Route 53 hosted zones with no DNS records."""

    def format_data(self, input: "Result") -> dict:
        """Format the data for the plugin.
        Args:
            input (Result): The input data to format.
        Returns:
            dict: The formatted data.
        """
        details = input.details["input"]
        pprint(details)

        # Initialize empty hosted zones list
        empty_hosted_zones = []

        # Check if hosted zones and records are present in the details
        zone_ids = set([zone["id"] for zone in details.get("hosted_zones", [])])
        record_zone_ids = set([record["zone_id"] for record in details.get("records", [])])

        # Find hosted zones that are not in the record zone IDs
        zone_ids.difference_update(record_zone_ids)

        empty_hosted_zones = [
            zone for zone in details.get("hosted_zones", [])
            if zone["id"] in zone_ids
        ]

        pprint(empty_hosted_zones)
        
        return {"empty_hosted_zones": empty_hosted_zones}

    def report_findings(self, data: "Result"):
        """Report the findings of the plugin.
        Attributes:
            data (CheckResult): The result of the checks.
        Returns:
            str: The formatted string containing the findings.
        """
        details = self.format_data(data)

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

        # Generate the result with formatted output
        if empty_zones:
            return Result(
                relates_to="r53",
                result_name="route53_empty_zones",
                result_description="Route 53 Hosted Zones with No Records",
                details=details,
                formatted=template.format(empty_zones=empty_zones_yaml),
            )
        else:
            return Result(
                relates_to="r53",
                result_name="route53_empty_zones",
                result_description="Route 53 Hosted Zones with No Records",
                details=details,
                formatted="No empty Route 53 hosted zones found.",
            )
