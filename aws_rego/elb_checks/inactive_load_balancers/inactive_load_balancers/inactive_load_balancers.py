from pluggy import HookimplMarker
import yaml
from loguru import logger
from opsbox import Result

# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")


class InactiveLoadBalancers:
    """Plugin for identifying inactive ELBs."""

    @hookimpl
    def report_findings(self, data: "Result"):
        """Format the check results in a LLM-readable format."""
        findings = data.details
        logger.debug(f"Findings: {findings}")

        inactive_load_balancers = []

        # Check for findings and collect inactive load balancers
        if findings and isinstance(findings, list):  # Ensure findings is a list
            inactive_load_balancers.extend(findings)

            # Template for displaying inactive load balancers
            template = """The following ELBs are inactive:
            
{load_balancers}"""

            # Format the output using the yaml dump for better display
            formatted_load_balancers = yaml.dump(inactive_load_balancers, default_flow_style=False)

            # Create the result item with the formatted data
            item = Result(
                relates_to="elb",
                result_name="inactive_load_balancers",
                result_description="Inactive Load Balancers",
                details=data.details,
                formatted=template.format(load_balancers=formatted_load_balancers)
            )

            return item
        else:
            return Result(
                relates_to="elb",
                result_name="inactive_load_balancers",
                result_description="Inactive Load Balancers",
                details=data.details,
                formatted="No inactive ELBs found."
            )
