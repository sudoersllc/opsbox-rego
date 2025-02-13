import contextlib
from pathlib import Path
from opsbox import PluginInfo, Registry, Result
from typing import TypedDict
import pluggy
import re
import json
from regopy import Interpreter


from loguru import logger

default_timeout = 20

hookspec = pluggy.HookspecMarker("opsbox")
hookimpl = pluggy.HookimplMarker("opsbox")


class RegoSpec:
    """Base contract for rego checks.

    Rego checks are plugins that process the data from providers, and can be used to apply checks
    and to transform the data."""

    @hookspec
    def report_findings(self, data: "Result") -> "Result":
        """Format the check results in a human-readable format.
        You would do this by adding the formatted results to the 'formatted' key of the result.
        """

    @hookspec
    def inject_data(self, data: "Result") -> "Result":
        """Inject data into the rego input.
        Normally, you would use this to inject data and arguments from a plugin's configuration into the input data.
        This is useful for passing arguments to the rego policy, which can use anything sent in from the input
        with the 'input' key.
        """


class RegoInfo(TypedDict):
    """A dictionary representing the details of a rego check.

    Attributes:
        description (str): The description of the check.
        rego_file (str): The name of the Rego file containing the check.
        gather_from (str): The name of the provider plugin to gather data from.
    """

    description: str
    rego_file: str
    gather_from: str


class RegoHandler:
    """Rego handler for rego plugins.

    Attributes:
        config (Config): The configuration for the handler.
    """

    @hookimpl
    def add_hookspecs(self, manager: pluggy.PluginManager) -> None:
        """Add the hookspecs to the manager."""
        manager.add_hookspecs(RegoSpec)

    @hookimpl
    def process_plugin(
        self, plugin: "PluginInfo", prior_results: list["Result"], registry: "Registry"
    ) -> list["Result"]:
        """Process the rego plugin.

        Args:
            plugin (PluginInfo): The plugin to process.
            prior_results (list[Result]): The results of previous plugins.
            registry (Registry): The plugin registry.

        Returns:
            list[Result]: The results of the plugin."""

        # grab data from providers
        input_data = self._grab_data_from_providers(plugin, registry)

        # apply data injection
        with contextlib.suppress(AttributeError):
            input_data = plugin.plugin_obj.inject_data(input_data)
            logger.debug(
                f"Data injected for plugin {plugin.name}.",
                extra={"after_inject": input_data},
            )

        # apply check
        result = self._execute_check(input_data, plugin)

        # format results
        result = plugin.plugin_obj.report_findings(result)
        return result

    def _extract_package_name(self, file_path):
        """
        Extracts the package name from a Rego file.

        Args:
            file_path (str): Path to the Rego file.

        Returns:
            str: The package name if found.

        Raises:
            ValueError: If the package name is not found in the file.
        """
        package_pattern = re.compile(r"^package\s+([a-zA-Z0-9_.]+)")

        with open(file_path, "r") as file:
            # Find the first line matching the package pattern
            for line in file:
                match = package_pattern.match(line.strip())
                if match:
                    return match.group(1)
        raise ValueError(f"Package name not found in {file_path}")

    def _grab_data_from_providers(
        self, plugin: PluginInfo, registry: Registry
    ) -> Result:
        """Grabs the data from the providers for the given plugin.

        Args:
            plugin (PluginInfo): The plugin to process.
            registry (Registry): The plugin registry.

        Returns:
            Result: The data from the providers."""
        # grab list of providers for the given plugin
        providers: list[PluginInfo] = [
            x
            for x in registry.active_plugins
            if (x.type == "provider") and (x.name in plugin.uses)
        ]

        # if we have no providers we can give no results
        if len(providers) < 1:
            logger.warning(
                f"No active provider found for rego plugin {plugin.name}. Using prior results."
            )
            result = None

        # if we have more than one provider we need to aggregate the results
        if len(providers) > 1:
            logger.debug(
                f"{len(providers)} providers found for rego plugin {plugin.name}: {[plugin.mame for plugin in providers]}. Building an aggregated result."
            )
            results: list[Result] = [
                provider.plugin_obj.gather_data() for provider in providers
            ]

            # build aggregated result metadata
            result_name = (
                f"[{', '.join([result.name for result in results])}]_aggregate"
            )
            description = (
                f"Aggregated data from {[provider.name for provider in providers]}."
            )
            relates_to = f"{', '.join([result.name for result in results])}"

            # aggregate details
            details = {}
            for result in results:
                details.update(result.details)

            logger.debug(
                f"Succesfully aggregated data from {[provider.name for provider in providers]}.",
                extra={"aggregated_provider_data": details},
            )

            result = Result(
                relates_to=relates_to,
                result_name=result_name,
                result_description=description,
                details=details,
            )
        else:  # we have only one provider, so grab from the 0th index
            logger.debug(
                f"Provider found for rego plugin {plugin.name}: {providers[0].name}."
            )
            provider = providers[0]
            result = provider.plugin_obj.gather_data()

            logger.debug(
                f"Input provider data gathered for plugin {plugin.name}.",
                extra={"provider_data": result.details},
            )

        return result

    def _execute_check(self, input_data: Result, plugin: PluginInfo) -> Result:
        """Applies a check to the given data using the rego-cpp interpreter.

        Args:
            data (Result): The data to apply the check to.
            plugin (PluginInfo): The plugin to apply the check from.

        Returns:
            list[Result]: The results of the check.
        """
        logger.info(
            f"Applying check {plugin.name} on input data.",
            extra={"input_data": input_data},
        )

        interpreter = Interpreter()  # set interpreter

        # grab rego info from plugin
        rego_info: RegoInfo = plugin.extra["rego"]
        rego_file_path = Path(plugin.toml_path).parent / rego_info["rego_file"]

        # get the package name from the rego file, used to build the query
        package_name = self._extract_package_name(rego_file_path)
        query = f"data.{package_name}.details"

        # load the rego policy
        with open(rego_file_path, "r") as rego_file:
            rego = rego_file.read()
            interpreter.add_module(package_name, rego)

        # load the input data
        input_data = json.dumps(input_data.details)
        interpreter.set_input_json(input_data)

        # run the query
        logger.debug(f"Running rego policy {rego_file_path} with query {query}.")
        result = interpreter.query("data")

        # grab the details from the result
        details = result[0][0]["details"]

        logger.success(
            f"Successfully applied check {plugin.name} to input data.",
            extra={"response": result},
        )

        default_text = "This is a partially filled result. The formatted text will be filled in later. If you see this text, there is an issue with the plugin."

        result = Result(
            relates_to=plugin.name,
            result_name=plugin.name,
            result_description=rego_info["description"],
            details=details,
            formatted=default_text,  # This will be filled in later
        )

        return result
