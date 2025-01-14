from pathlib import Path
from pydantic import BaseModel, Field
import requests
from core.plugins import PluginInfo, Registry, Result
from typing import TypedDict
from contextlib import contextmanager
import pluggy
import re

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
        """Format the check results in a human-readable format."""


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


class Config(BaseModel):
    """Configuration for the Rego handler.

    Attributes:
        opa_url (str): The URL of the OPA server to upload and apply Rego policies.
    """

    opa_url: str = Field(..., description="The URL of the OPA server to upload and apply Rego policies.", required=True)


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
    def grab_config(self) -> type[BaseModel]:
        """Return the configuration model for the plugin."""
        return Config

    @hookimpl
    def set_data(self, model: "Config") -> None:
        """Set the data for the plugin based on the model."""
        self.config = model

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
        # grab rego info from plugin
        base_url = self.config.opa_url
        rego_info: RegoInfo = plugin.extra["rego"]
        rego_file_path = Path(plugin.toml_path).parent / rego_info["rego_file"]

        # grab data from provider
        providers: list[PluginInfo] = [
            x for x in registry.produce_pipeline().dependencies if (x.type == "provider") and (x.name in plugin.uses)
        ]

        if len(providers) == 0:
            logger.warning(f"No provider found for rego plugin {plugin.name}. Using empty data.")
            logger.debug(f"Plugin uses: {plugin.uses}")
            data = prior_results[0] if prior_results else Result(relates_to=plugin.name, result_name=plugin.name, result_description="", details={})
        elif len(providers) > 1:
            raise Exception("Rego plugins can only use one provider.")
        else:
            data = providers[0].plugin_obj.gather_data()
        # apply check
        with self.temp_policy(plugin, rego_file_path, base_url) as _:
            result = self.apply_check(data, plugin, rego_file_path, base_url)
            result = plugin.plugin_obj.report_findings(result)
        return result
    
    def extract_package_name(self, file_path):
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

        with open(file_path, 'r') as file:
            # Find the first line matching the package pattern
            for line in file:
                match = package_pattern.match(line.strip())
                if match:
                    print(match.group(1))
                    return match.group(1)
        raise ValueError(f"Package name not found in {file_path}")

    @contextmanager
    @logger.catch(reraise=True)
    def temp_policy(self, plugin: PluginInfo, rego_path: Path, base_url: str):
        """Upload a policy to OPA server and remove it after use.

        Args:
            plugin (PluginInfo): The plugin to process.
            rego_path (Path): The path to the Rego file.
            base_url (str): The base URL of the OPA server.
        """
        info: RegoInfo = plugin.extra["rego"]

        package_name = self.extract_package_name(rego_path)
        package_name_path = package_name.replace(".", "/")
        package_url = f"{base_url}/v1/policies/{package_name_path}"
        logger.debug(f"Uploading policy {info['rego_file']} with package name {package_name} to OPA server {base_url}")
        with open(rego_path, "r") as rego_file:
            policy_data = rego_file.read()
            resp = requests.put(
                package_url,
                data=policy_data,
                headers={"Content-Type": "text/plain"},
                timeout=default_timeout,
            )

            # check for success
            logger.debug(f"Policy upload response: {resp.status_code}")
            if resp.status_code != 200:
                logger.error(f"Policy upload failed: {resp.text}")
                raise Exception(f"Policy upload failed: {resp.text}")
            else:
                logger.success(f"Policy {info['rego_file']} uploaded successfully.")
        yield

        logger.debug(f"Removing policy {info['rego_file']}  on OPA server {base_url}")
        resp = requests.delete(
            package_url,
            headers={"Content-Type": "text/plain"},
            timeout=default_timeout,
        )

        # check for success
        if resp.status_code != 200:
            logger.error(f"Policy removal failed: {resp.text}")
            raise Exception(f"Policy removal failed: {resp.text}")
        else:
            logger.success(f"Policy {info['rego_file']} removed successfully.")

    def apply_check(self, data: "Result", plugin: PluginInfo, rego_file_path: str, base_url: str) -> list["Result"]:
        """Applies a set of registered checks to the given data using Open Policy Agent (OPA).

        Args:
            data (Result): The data to apply the checks to.
            plugin (PluginInfo): The plugin to apply the checks from.
            rego_file_path (str): The path to the Rego file.
            base_url (str): The base URL of the OPA server
        Returns:
            list[Result]: The results of the checks.
        """
        # get rego info
        check: RegoInfo = plugin.extra["rego"]

        # grab upload, apply urls
        data = data.details
        package_name = self.extract_package_name(rego_file_path)
        package_name_path = package_name.replace(".", "/")
        opa_url = f"{base_url}/v1/data/{package_name_path}"

        # Query OPA
        response = requests.post(opa_url, json=data, timeout=default_timeout)
        response_data = response.json()

        # Log Results
        logger.debug(f"OPA URL: {opa_url}")
        logger.debug(f"OPA response status code: {response.status_code}")
        if response.status_code != 200:
            logger.error(f"OPA response: {response_data}")

        else:
            logger.success(f"OPA successfully queried for check {check['rego_file']}.")

        decision = response_data.get("result", False)
        result_details = decision.get("details", []) if isinstance(decision, dict) else []
        logger.success(decision)
        result = Result(
            relates_to=plugin.name,
            result_name=plugin.name,
            result_description=check["description"],
            details=result_details,
            formatted="",  # This will be filled in later
        )

        return result
