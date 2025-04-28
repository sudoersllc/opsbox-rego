from pluggy import HookimplMarker
import yaml
from opsbox import Result
from pydantic import BaseModel, Field
from typing import Annotated

# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")


class InactiveLoadBalancersConfig(BaseModel):
    elb_inactive_requests_threshold: Annotated[
        int,
        Field(
            default=0,
            description="# of requests below which to consider an ELB to be inactive. Default = 0.",
        ),
    ]


class InactiveLoadBalancers:
    """Plugin for identifying inactive ELBs."""

    @hookimpl
    def grab_config(self) -> type[BaseModel]:
        """Return the plugin's configuration pydantic model.
        These should be things your plugin needs/wants to function.

        Returns:
            type[BaseModel]: The configuration model for the plugin."""
        return InactiveLoadBalancersConfig

    @hookimpl
    def set_data(self, model: type[BaseModel]) -> None:
        """Set the data for the plugin based on the model.

        Args:
            model (BaseModel): The model containing the data for the plugin."""
        self.conf = model.model_dump()

    def format_data(self, input: Result) -> dict:
        """Format the input data to extract inactive load balancers.

        Args:
            input (Result): The input data containing ELB details.

        Returns:
            dict: A dictionary containing details of inactive load balancers.
        """
        lbs = input.details.get("input").get("elbs", [])
        inactive = []


        for load_balancer in lbs:
            if load_balancer.get("State", load_balancer.get("state")) == "inactive":
                inactive.append(load_balancer)
            elif (
                load_balancer.get("RequestCount", load_balancer.get("request_count", 0))
                <= self.conf["elb_inactive_requests_threshold"]):
                inactive.append(load_balancer)

        return inactive

    @hookimpl
    def report_findings(self, data: Result):
        """Format the check results in a readable format.

        Args:
            data (Result): The data containing ELB details.

        Returns:
            Result: The formatted result with inactive ELBs.
        """
        
        findings = self.format_data(data)


        # Check for findings and collect inactive load balancers
        if findings is not None:

            # Template for displaying inactive load balancers
            template = """The following ELBs are inactive:
            
{load_balancers}"""

            # Format the output using the yaml dump for better display
            formatted_load_balancers = yaml.dump(
                findings, default_flow_style=False
            )

            # Create the result item with the formatted data
            item = Result(
                relates_to="elb",
                result_name="inactive_load_balancers",
                result_description="Inactive Load Balancers",
                details=findings,
                formatted=template.format(load_balancers=formatted_load_balancers),
            )

            return item
        else:
            return Result(
                relates_to="elb",
                result_name="inactive_load_balancers",
                result_description="Inactive Load Balancers",
                details=[],
                formatted="No inactive ELBs found.",
            )
