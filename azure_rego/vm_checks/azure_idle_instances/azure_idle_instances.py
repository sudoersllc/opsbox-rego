import yaml
from loguru import logger
from opsbox import Result
from pydantic import BaseModel, Field
from typing import Annotated
from pluggy import HookimplMarker

# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")


class AzureIdleVMsConfig(BaseModel):
    azure_vm_cpu_idle_threshold: Annotated[
        int,
        Field(
            default=1,
            description="The % threshold for the average CPU utilization of an Azure VM to be considered idle. Default is 1.",
        ),
    ]


class IdleVMs:
    """Plugin for identifying idle Azure VMs."""

    @hookimpl
    def grab_config(self) -> type[BaseModel]:
        """Return the plugin's configuration pydantic model.
        These are the settings required for the plugin to function."""
        return AzureIdleVMsConfig

    @hookimpl
    def set_data(self, model: type[BaseModel]) -> None:
        """Set the data for the plugin based on the provided configuration model.

        Args:
            model (BaseModel): The model containing the plugin configuration.
        """
        self.conf = model.model_dump()

    @hookimpl
    def inject_data(self, data: "Result") -> "Result":
        """Inject configuration data into the plugin's input.

        Args:
            data (Result): The data to inject configuration into.

        Returns:
            Result: The data with the injected configuration values.
        """
        data.details["input"]["azure_vm_cpu_idle_threshold"] = self.conf[
            "azure_vm_cpu_idle_threshold"
        ]
        return data

    @hookimpl
    def report_findings(self, data: Result) -> Result:
        """Report the findings of idle Azure VMs.

        Args:
            data (Result): The result object containing the checked data.

        Returns:
            Result: A formatted result with the idle VMs details.
        """
        findings = data.details
        logger.debug(f"Findings: {findings}")
        vms = []
        for vm in findings:
            vm_obj = {
                vm["vm_id"]: {
                    "location": vm["location"],
                    "power_state": vm.get("power_state", "running"),
                    "avg_cpu_utilization": vm["avg_cpu_utilization"],
                    "vm_size": vm["vm_size"],
                    "operating_system": vm.get("operating_system", "N/A"),
                    "tags": vm.get("tags", {}),
                }
            }
            vms.append(vm_obj)
        try:
            vm_yaml = yaml.dump(vms, default_flow_style=False)
        except Exception as e:
            logger.error(f"Error formatting VM details: {e}")

        template = """The following Azure VMs are idle, with an average CPU utilization below the defined threshold.
The data is presented in the following format:

{vms}"""

        if findings:
            formatted = template.format(vms=vm_yaml)
        else:
            formatted = "No idle Azure VMs found."

        item = Result(
            relates_to="azure_vm",
            result_name="idle_vms",
            result_description="Idle Azure VMs",
            details=data.details,
            formatted=formatted,
        )
        return item
