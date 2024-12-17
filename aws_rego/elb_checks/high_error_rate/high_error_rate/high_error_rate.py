from pluggy import HookimplMarker
import yaml
from loguru import logger
from core.plugins import Result

# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")


class HighErrorRate:
    """Plugin for identifying ELBs with high error rates."""

    @hookimpl
    def report_findings(self, data: "Result"):
        """Report the findings of the plugin.
        Attributes:
            data (CheckResult): The result of the checks.
        Returns:
            str: The formatted string containing the findings.
        """
        findings = data.details

        if not findings:
            return Result(
                relates_to="elb",
                result_name="high_error_rate",
                result_description="High Error Rate Load Balancers",
                details=data.details,
                formatted="No high error rate load balancers found.",
            )

        high_error_rate_load_balancers = []
        if findings:
            load_balancers = findings.get("high_error_rate_load_balancers", [])
            for lb in load_balancers:
                logger.debug(f"Processing load balancer: {lb}")
                if isinstance(lb, dict) and "name" in lb and "type" in lb and "error_rate" in lb:
                    lb_obj = {lb["name"]: {"type": lb["type"], "error_rate": lb["error_rate"]}}
                    high_error_rate_load_balancers.append(lb_obj)
        template = """The following ELBs have high error rates:
            \n
            {load_balancers}
        """

        item = Result(
            relates_to="elb",
            result_name="high_error_rate",
            result_description="High Error Rate Load Balancers",
            details=data.details,
            formatted=template.format(
                load_balancers=yaml.dump(high_error_rate_load_balancers, default_flow_style=False)
            ),
        )

        return item
