from pluggy import HookimplMarker
import yaml
from core.plugins import Result
import logging as logger

# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")


class LowRequestCount:
    """Plugin for identifying ELBs with low request counts."""

    @hookimpl
    def report_findings(self, data: "Result"):
        """Format the check results in a LLM-readable format."""
        findings = data.details
        logger.debug(f"Findings: {findings}")

        if not findings:
            return Result(
                relates_to="elb",
                result_name="low_request_count",
                result_description="Low Request Count",
                details=data.details,
                formatted="No ELBs with low request counts found.",
            )

        inactive_load_balancers = []
        
        # Assuming findings is a list of ELB dictionaries
        for lb in findings:
            inactive_load_balancers.append(lb)

        template = """The following ELBs have low request counts:

{load_balancers}"""

        formatted_load_balancers = yaml.dump(inactive_load_balancers, default_flow_style=False)

        item = Result(
            relates_to="elb",
            result_name="low_request_count",
            result_description="Low Request Count",
            details=data.details,
            formatted=template.format(load_balancers=formatted_load_balancers),
        )
        return item
