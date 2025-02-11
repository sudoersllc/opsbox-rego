from pluggy import HookimplMarker
import yaml
from opsbox import Result
import logging as logger
from pydantic import BaseModel, Field
from typing import Annotated

# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")


class ELBLowRequestsConfig(BaseModel):
    elb_low_requests_threshold: Annotated[
        int,
        Field(
            default=0,
            description="# of requests below which to consider an ELB to have low request counts. Default = 100.",
        ),
    ]


class LowRequestCount:
    """Plugin for identifying ELBs with low request counts."""

    @hookimpl
    def grab_config(self) -> type[BaseModel]:
        """Return the plugin's configuration pydantic model.
        These should be things your plugin needs/wants to function.

        Returns:
            type[BaseModel]: The configuration model for the plugin."""
        return ELBLowRequestsConfig

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
        data.details["input"]["elb_low_requests_threshold"] = self.conf[
            "elb_low_requests_threshold"
        ]
        return data

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

        formatted_load_balancers = yaml.dump(
            inactive_load_balancers, default_flow_style=False
        )

        item = Result(
            relates_to="elb",
            result_name="low_request_count",
            result_description="Low Request Count",
            details=data.details,
            formatted=template.format(load_balancers=formatted_load_balancers),
        )
        return item
