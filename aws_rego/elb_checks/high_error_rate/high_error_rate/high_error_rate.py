from pluggy import HookimplMarker
import yaml
from loguru import logger
from opsbox import Result

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

        high_error_rate_load_balancers = []
        if findings:
            load_balancers = findings.get("high_error_rate_load_balancers", [])
            for lb in load_balancers:
                logger.debug(f"Processing load balancer: {lb}")
                if isinstance(lb, dict) and "name" in lb and "type" in lb and "error_rate" in lb:
                    lb_obj = {lb["name"]: {"type": lb["type"], "error_rate": lb["error_rate"]}}
                    high_error_rate_load_balancers.append(lb_obj)
                else:
                    logger.error(f"Invalid load balancer data: {lb}")
        
            template = """The following ELBs have a high error rate: \n
            {load_balancers}"""
            try:
                load_balancers_yaml = yaml.dump(high_error_rate_load_balancers, default_flow_style=False)
            except Exception as e:
                logger.error(f"Error formatting load balancer details: {e}")

            formatted = template.format(load_balancers=load_balancers_yaml)

            return Result(
                relates_to="elb",
                result_name="high_error_rate",
                result_description="High Error Rate Load Balancers",
                details=data.details,
                formatted=formatted,
            )
        else:
            return Result(
                relates_to="elb",
                result_name="high_error_rate",
                result_description="High Error Rate Load Balancers",
                details=data.details,
                formatted="No ELBs with high error rates found.",
           )
            
        

