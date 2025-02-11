from pluggy import HookimplMarker, HookspecMarker, PluginManager
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from opsbox import PluginInfo, Result, Registry
    from typing import Any
from loguru import logger


# Define a hookimpl (implementation of the contract)
hookspec = HookspecMarker("opsbox")


class ProviderSpec:
    """Base contract for providers.
    Providers are plugins that gather data from a source, like AWS, Azure, etc."""

    @hookspec
    def gather_data(self) -> "Result":
        """Gather data for the plugin."""


class OutputSpec:
    """Base contract for outputs.
    Outputs are plugins that process the data from the providers."""

    @hookspec
    def proccess_results(self, results: list["Result"]) -> None:
        """Output the data from the plugin."""


class AssistantSpec:
    """Base contract for assistants.
    Assistants are plugins that help with various tasks, normally used right before the output."""

    @hookspec
    def proccess_input(self, input: list["Result"]) -> list["Result"]:  # noqa: A002
        """Process the input and return the processed input.

        Args:
            input (str|list[str]): The human-readable input to process."""


class InputSpec:
    """Base contract for inputs.
    Inputs are plugins that process the data from the providers."""

    @hookspec
    def process(self, data: list["Result"]) -> None:
        """Process the results from the plugin."""


hookimpl = HookimplMarker("opsbox")


class GeneralHandler:
    """General handler for python plugins."""

    @hookimpl
    def add_hookspecs(self, manager: PluginManager):
        """Add the hookspecs to the manager."""
        manager.add_hookspecs(AssistantSpec)
        manager.add_hookspecs(OutputSpec)
        manager.add_hookspecs(ProviderSpec)
        manager.add_hookspecs(InputSpec)
        return AssistantSpec, OutputSpec, ProviderSpec, InputSpec

    @hookimpl
    def process_plugin(
        self, plugin: "PluginInfo", prior_results: list["Result"], registry: "Registry"
    ) -> Any:
        """Process the plugin."""
        logger.debug(f"GeneralHandler processing plugin {plugin.name}")
        if plugin.type == "input":
            providers: list["PluginInfo"] = [
                x
                for x in registry.active_plugins
                if (x.type == "provider") and (x.name in plugin.uses)
            ]
            data = []
            for x in providers:
                data.append(x.plugin_obj.gather_data())
            return plugin.plugin_obj.process(data)
        elif plugin.type == "output":
            return plugin.plugin_obj.proccess_results(prior_results)
        elif plugin.type == "assistant":
            return plugin.plugin_obj.proccess_input(prior_results)
        return None
