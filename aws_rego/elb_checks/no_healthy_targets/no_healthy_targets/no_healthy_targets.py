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
        findings = data
        logger.debug(f"Findings: {findings}")

        unhealthy_targets = []

        # Check for findings and collect inactive load balancers
        if findings and isinstance(findings, list):  # Ensure findings is a list
            unhealthy_targets.extend(findings)

            # Template for displaying inactive load balancers
            template = """
            The following ELBs are unhealthy:

            {load_balancers}
            """

            # Format the output using the yaml dump for better display
            formatted_load_balancers = yaml.dump(unhealthy_targets, default_flow_style=False)

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
                result_description="ELBs with no healthy targets",
                details=data.details,
                formatted="No ELBs with only unhealthy targets found."
            )
