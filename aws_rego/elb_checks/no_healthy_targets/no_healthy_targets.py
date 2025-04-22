from pluggy import HookimplMarker
import yaml
from loguru import logger
from opsbox import Result

# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")


class NoHealthyTargets:
    """Plugin for identifying elbs with no healthy targets."""

    def format_data(self, input: Result) -> dict:
        """Format the input data to extract ELBs with no healthy targets.

        Args:
            input (Result): The input data containing ELB details.

        Returns:
            list: A list of ELBs with no healthy targets.
        """
        lbs = input.details.get("input").get("elbs", [])
        no_healthy_targets = []

        for load_balancer in lbs:
            health = load_balancer.get("InstanceHealth", load_balancer.get("instance_health"))

            bool_list = [x.get("State", x.get("state")) == "unhealthy" for x in health]
            if all(bool_list):
                no_healthy_targets.append(load_balancer)

        return no_healthy_targets

    @hookimpl
    def report_findings(self, data: "Result"):
        """Format the check results in a LLM-readable format."""
        findings = self.format_data(data)

        no_healthy_targets = []

        # Check for findings and collect inactive load balancers
        if findings and isinstance(findings, list):  # Ensure findings is a list
            no_healthy_targets.extend(findings)

            # Template for displaying inactive load balancers
            template = """The following ELBs have no healthy targets:

{load_balancers}"""

            # Format the output using the yaml dump for better display
            formatted_load_balancers = yaml.dump(
                no_healthy_targets, default_flow_style=False
            )

            # Create the result item with the formatted data
            item = Result(
                relates_to="elb",
                result_name="no_healthy_targets",
                result_description="ELBs with no healthy targets",
                details=findings,
                formatted=template.format(load_balancers=formatted_load_balancers),
            )

            return item
        else:
            return Result(
                relates_to="elb",
                result_name="no_healthy_targets",
                result_description="No Healthy Targets",
                details=[],
                formatted="No ELBs found with no healthy targets.",
            )
