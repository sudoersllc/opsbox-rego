from typing import Annotated
from pluggy import HookimplMarker
import yaml
from loguru import logger
from opsbox import Result
from pydantic import BaseModel, Field

# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")


class Config(BaseModel):
    cpu_percent_upper_bound: Annotated[
        int,
        Field(
            default=0,
            description="Upper bound for cpu percent.",
        ),
    ]


class HighCPUPercent:
    """Plugin for identifying Azure DBs with high cpu rates."""

    @hookimpl
    def grab_config(self) -> type[BaseModel]:
        """Return the plugin's configuration pydantic model.
        These should be things your plugin needs/wants to function."""
        return Config

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
        findings: dict = data.details

        server_metrics_list = []

        for x in findings["azure_sql_dbs"]:
            cursor = {}
            uri = x["uri"]
            del x["uri"]
            cursor[uri] = x
            server_metrics_list.append(cursor)
            

        template = """The following Azure SQL dbs have high average cpu usage: \n
        {info}"""
        try:
            info = yaml.dump(
                server_metrics_list, default_flow_style=False
            )
        except Exception as e:
            logger.error(f"Error formatting azure sql details: {e}")

            formatted = template.format(info=info)

            return Result(
                relates_to="azure_sql_db",
                result_name="high_cpu_percent",
                result_description="High CPU Percent Azure SQL DBs",
                details=data.details,
                formatted=formatted,
            )
        
    @hookimpl
    def inject_data(self, data: "Result") -> "Result":
        """Inject data into the plugin.

        Args:
            data (Result): The data to inject into the plugin.

        Returns:
            Result: The data with the injected values.
        """
        data.details["input"]["cpu_upper_bound_threshold"] = self.conf[
            "cpu_upper_bound_threshold"
        ]
        return data
