from pluggy import HookimplMarker
import yaml
from loguru import logger
from core.plugins import Result

# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")


class NoHealthyTargets:
    """Plugin for identifying elbs with no healthy targets."""

    @hookimpl
    def report_findings(self, data: "Result"):
        """Format the check results in a LLM-readable format."""
        findings = data.details
        logger.debug(f"Findings: {findings}")

        no_healthy_targets = []

        # Check for findings and collect inactive load balancers
        if findings and isinstance(findings, list):  # Ensure findings is a list
            no_healthy_targets.extend(findings)

            # Template for displaying inactive load balancers
            template = """The following ELBs have no healthy targets:

{load_balancers}"""

            # Format the output using the yaml dump for better display
            formatted_load_balancers = yaml.dump(no_healthy_targets, default_flow_style=False)


            # Create the result item with the formatted data
            item = Result(
                relates_to="elb",
                result_name="no_healthy_targets",

                result_description="ELBs with no healthy targets",
                details=data.details,
                formatted=template.format(load_balancers=formatted_load_balancers)
            )

            return item
        else:
            return Result(
                relates_to="elb",
                result_name="no_healthy_targets",
                result_description="No Healthy Targets",
                details=data.details,
                formatted="No ELBs found with no healthy targets."

            )
