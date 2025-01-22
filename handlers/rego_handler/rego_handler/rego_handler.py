from pathlib import Path
from pydantic import BaseModel, Field
import requests
from core.plugins import PluginInfo, Registry, Result
from typing import TypedDict
from contextlib import contextmanager
import pluggy
import re
import subprocess
import json
import tempfile
import os
from pathlib import Path

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
        # with self.temp_policy(plugin, rego_file_path, base_url) as _:
        result = self.apply_check(data, plugin, rego_file_path)
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


    def apply_check(self, data: "Result", plugin: PluginInfo, rego_file_path: str) -> list["Result"]:
        """Applies a set of registered checks to the given data using the OPA eval command."""
        logger.success(f"Rego file path: {rego_file_path}")
        check: RegoInfo = plugin.extra["rego"]

        # Prepare data and command for OPA eval
        data = data.details
        package_name = self.extract_package_name(rego_file_path)

        logger.success(f"Package name: {package_name}")
        temp_input_file_path = None
        try:
            # Write the input JSON to a temporary file in text mode
            with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix=".json", encoding='utf-8') as temp_input_file:
                json.dump(data['input'], temp_input_file)
                temp_input_file_path = temp_input_file.name

            logger.debug(f"Temporary input file path: {temp_input_file_path}")
            with open(temp_input_file_path, 'r', encoding='utf-8') as f:
                logger.debug(f"Input file content:\n{f.read()}")

            opa_eval_command = [
                "opa", "eval",
                f"data.aws_rego.ec2_checks.stray_ebs.stray_ebs",  # Adjust the query
                "--data", str(rego_file_path),
                "--input", str(temp_input_file_path),
                "--format=json"  # Add pretty format for debugging if needed
            ]

            # Debugging the command
            logger.debug(f"Running OPA command: {' '.join(opa_eval_command)}")

            # Run the OPA eval command
            process = subprocess.run(
                opa_eval_command,
                text=True,
                capture_output=True,
                check=True
            )

            # Parse the output
            cli_output = process.stdout
            cli_result = json.loads(cli_output)

            # Extract decision results
            expressions = cli_result.get("result", [])[0].get("expressions", [])
            if expressions:
                decision = expressions[0].get("value", {})
                result_details = decision.get("details", [])
            else:
                decision = {}
                result_details = []

            logger.success(f"OPA eval successfully executed for {check['rego_file']}.")

        except subprocess.CalledProcessError as e:
            logger.error(f"OPA eval failed: {e}")
            logger.error(f"OPA eval stderr: {e.stderr}")
            decision = {}
            result_details = []

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OPA eval output: {e}")
            decision = {}
            result_details = []

        except Exception as e:
            logger.error(f"Error running OPA eval: {e}")
            decision = {}
            result_details = []

        finally:
            # Clean up the temporary file
            if temp_input_file_path and os.path.exists(temp_input_file_path):
                os.remove(temp_input_file_path)

        # Create and return Result object
        result = Result(
            relates_to=plugin.name,
            result_name=plugin.name,
            result_description=check["description"],
            details=result_details,
            formatted="",  # This will be filled in later
        )

        return result
