import yaml
from loguru import logger
from core.plugins import Result


class UnattachedEips:
    """Formatting for the unattached_eips rego check."""

    def report_findings(self, data: Result):
        """Report the findings of the plugin.
        Attributes:
            data (CheckResult): The result of the checks.
        Returns:
            str: The formatted string containing the findings.
        """
        eips = []
        formatted = ""
        for eip in data.details:
            eips.append(eip)
            try:
                eips_yaml = yaml.dump(eips, default_flow_style=False)
            except Exception as e:
                logger.error(f"Error formatting volume details: {e}")
            template = """The Eips are Unattached. 

            {eips}"""

        formatted = template.format(eips=eips_yaml) if eips else "No unattached EIPs"

        item = Result(
            relates_to="ec2",
            result_name="unattached_eips",
            result_description="Unattached EIPs",
            details=data.details,
            formatted=formatted,
        )
        return item
