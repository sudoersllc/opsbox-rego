from typing import Annotated
from pluggy import HookimplMarker
import yaml
from loguru import logger
from opsbox import Result
from pydantic import BaseModel, Field
import re

# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")

def split_words(key: str) -> list[str]:
    """Splits a key into a list of lowercase words."""
    if "_" in key:
        return key.lower().split("_")
    words = re.sub(r'(?<!^)(?=[A-Z])', ' ', key).split()
    return [word.lower() for word in words]

def convert_case(key: str, target: str) -> str:
    """Convert a key string to the desired casing style."""
    def to_snake_case(words: list[str]) -> str:
        return "_".join(words)

    def to_camel_case(words: list[str]) -> str:
        return words[0] + "".join(word.capitalize() for word in words[1:])

    def to_pascal_case(words: list[str]) -> str:
        return "".join(word.capitalize() for word in words)

    def to_upper_case(words: list[str]) -> str:
        return "_".join(words).upper()

    def to_lower_case(words: list[str]) -> str:
        return "".join(words)
    
    words = split_words(key)
    match target:
        case "snake_case":
            return to_snake_case(words)
        case "camelCase":
            return to_camel_case(words)
        case "PascalCase":
            return to_pascal_case(words)
        case "UPPERCASE":
            return to_upper_case(words)
        case "lowercase":
            return to_lower_case(words)
        case _:
            raise ValueError(f"Unknown target case: {target}")

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

    def format_data(self, input: "Result") -> dict:
        """Format the data for the plugin.

        Args:
            input (Result): The input data to format.

        Returns:
            dict: The formatted data.
        """
        details = input.details["input"]

        load_balancers = []

        for lb in details["elbs"]:
            lb_obj = {convert_case(k, "PascalCase"): v for k, v in lb.items()}
            load_balancers.append(lb_obj)
        
        high_error_rate_load_balancers = []
        for load_balancer in load_balancers:
            if (
                load_balancer.get("ErrorRate")
                >= self.conf["elb_error_rate_threshold"]
            ):
                high_error_rate_load_balancers.append(load_balancer)

        details = high_error_rate_load_balancers
        return details

    @hookimpl
    def report_findings(self, data: "Result"):
        """Report the findings of the plugin.
        Attributes:
            data (CheckResult): The result of the checks.
        Returns:
            str: The formatted string containing the findings.
        """
        findings = self.format_data(data)

        high_error_rate_load_balancers = []
        if findings:
            high_error_rate_load_balancers = findings
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
                details=high_error_rate_load_balancers,
                formatted=formatted,
            )
        else:
            return Result(
                relates_to="elb",
                result_name="high_error_rate",
                result_description="High Error Rate Load Balancers",
                details=[],
                formatted="No ELBs with high error rates found.",
            )