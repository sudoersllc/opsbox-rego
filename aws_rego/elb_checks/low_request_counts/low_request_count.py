from pluggy import HookimplMarker
import yaml
from core.plugins import Result

# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")


class LowRequestCount:
    """Plugin for identifying ELBs with low request counts."""

    @hookimpl
    def report_findings(self, data: "Result"):
        """Format the check results in a LLM-readable format."""
        findings = data.details

        if not findings:
            return Result(
                relates_to="elb",
                result_name="low_request_count",
                result_description="Low Request Count",
                details=data.details,
                formatted="No ELBs with low request counts found.",
            )
        

        inactive_load_balancers = []
        if findings:
            load_balancers = findings.get("elbs", [])
            for lb in load_balancers:
                inactive_load_balancers.append(lb)
        template = """The following ELBs have low request counts:
            \n
            {load_balancers}
        """

        item = Result(
            relates_to="elb",
            result_name="low_request_count",
            result_description="Low Request Count",
            details=data.details,
            formatted=template.format(load_balancers=yaml.dump(inactive_load_balancers, default_flow_style=False)),
        )
        return item
