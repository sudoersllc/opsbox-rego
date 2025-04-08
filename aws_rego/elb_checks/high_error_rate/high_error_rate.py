from typing import Annotated
from pluggy import HookimplMarker
import yaml
from loguru import logger
from opsbox import Result
from pydantic import BaseModel, Field

# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")


class HighELBErrorRateConfig(BaseModel):
    elb_error_rate_threshold: Annotated[
        int,
        Field(
            default=0,
            description="# of errors needed to consider an ELB to have a high error rate.",
        ),
    ]


class HighErrorRate:
    """Plugin for identifying ELBs with high error rates."""

    @hookimpl
    def grab_config(self) -> type[BaseModel]:
        """Return the plugin's configuration pydantic model.
        These should be things your plugin needs/wants to function."""
        return HighELBErrorRateConfig

    @hookimpl
    def set_data(self, model: type[BaseModel]) -> None:
        """Set the data for the plugin based on the model.

        Args:
            model (BaseModel): The model containing the data for the plugin."""
        self.conf = model.model_dump()

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
            if findings is type(dict):
                load_balancers = findings.get("high_error_rate_load_balancers", [])
            else:
                load_balancers = findings
            for lb in load_balancers:
                if (
                    isinstance(lb, dict)
                    and "name" in lb
                    and "type" in lb
                    and "error_rate" in lb
                ):
                    lb_obj = {
                        lb["name"]: {"type": lb["type"], "error_rate": lb["error_rate"]}
                    }
                    high_error_rate_load_balancers.append(lb_obj)
                elif (
                    isinstance(lb, dict)
                    and "Name" in lb
                    and "Type" in lb
                    and "ErrorRate" in lb
                ):
                    lb_obj = {
                        lb["Name"]: {"type": lb["Type"], "error_rate": lb["ErrorRate"]}
                    }
                    high_error_rate_load_balancers.append(lb_obj)
                else:
                    name: str
                    if lb.get("name") is not None:
                        name = lb["name"]
                        pass
                    elif lb.get("Name") is not None:
                        name = lb["Name"]
                        pass

                    logger.error(f"Invalid load balancer data for {name}", extra=lb)

            template = """The following ELBs have a high error rate: \n
            {load_balancers}"""
            try:
                load_balancers_yaml = yaml.dump(
                    high_error_rate_load_balancers, default_flow_style=False
                )
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

    @hookimpl
    def inject_data(self, data: "Result") -> "Result":
        """Inject data into the plugin.

        Args:
            data (Result): The data to inject into the plugin.

        Returns:
            Result: The data with the injected values.
        """
        data.details["input"]["elb_error_rate_threshold"] = self.conf[
            "elb_error_rate_threshold"
        ]
        return data
