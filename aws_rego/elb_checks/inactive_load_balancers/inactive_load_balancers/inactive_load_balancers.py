from pluggy import HookimplMarker
import yaml
from loguru import logger
from core.plugins import Result
from pydantic import BaseModel, Field
from typing import Annotated

# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")


class InactiveLoadBalancersConfig(BaseModel):
    elb_inactive_requests_threshold: Annotated[int, Field(default = 0, description="# of requests below which to consider an ELB to be inactive. Default = 0.")]



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

    @hookimpl
    def inject_data(self, data: "Result") -> "Result":
        """Inject data into the plugin.

        Args:
            data (Result): The data to inject into the plugin.

        Returns:
            Result: The data with the injected values.
        """
        data.details["input"]["elb_inactive_requests_threshold"] = self.conf["elb_inactive_requests_threshold"]
        return data

    @hookimpl
    def report_findings(self, data: "Result"):
        """Format the check results in a LLM-readable format."""
        findings = data.details
        logger.debug(f"Findings: {findings}")

        inactive_load_balancers = []

        # Check for findings and collect inactive load balancers
        if findings is not None:
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
 