import contextlib
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
    def grab_config(self) -> type[BaseModel]:
        """Return the configuration model.

        Returns:
            type[RegoHandlerConfig]: The configuration model for the plugin.
        """

        class RegoHandlerConfig(BaseModel):
            """Configuration for the Rego handler.

            Attributes:
                opa_url (str | None): The URL of the OPA server to upload and apply Rego policies. If not provided, the policies will be applied locally.
            """

            opa_url: str | None = Field(
                default=None,
                description="The URL of the OPA server to upload and apply Rego policies. If not provided, the policies will be applied locally.",
            )

        return RegoHandlerConfig

    @hookimpl
    def set_data(self, model: type[BaseModel]) -> None:
        """Set the data for the plugin based on the model."""
        self.config = model

        # fix slash issues
        if self.config.opa_url is not None:
            self.config.opa_url = self.config.opa_url.rstrip("/")

        # double check OPA existence
        self._double_check_opa_existence(self.config.opa_url)

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
        rego_info: RegoInfo = plugin.extra["rego"]
        rego_file_path = Path(plugin.toml_path).parent / rego_info["rego_file"]

        # grab list of providers
        providers: list[PluginInfo] = [
            x
            for x in registry.produce_pipeline().dependencies
            if (x.type == "provider") and (x.name in plugin.uses)
        ]

        if len(providers) == 1:
            provider = providers[0]
            input_data = provider.plugin_obj.gather_data()
        if len(providers) > 1:
            raise RuntimeError("Rego plugins can only use one provider.")
        if len(providers) == 0:
            logger.warning(
                f"No provider found for rego plugin {plugin.name}. Using empty data."
            )
            logger.trace(f"Plugin {plugin.name} uses: {plugin.uses}")

            input_data = (
                prior_results[0]
                if prior_results
                else Result(
                    relates_to=plugin.name,
                    result_name=plugin.name,
                    result_description="",
                    details={},
                )
            )

        # apply data injection
        with contextlib.suppress(AttributeError):
            input_data = plugin.plugin_obj.inject_data(input_data)
            logger.debug(f"Data injected for plugin {plugin.name}.")
            logger.trace(f"Injected data: {input_data}")
        # apply check
        if self.config.opa_url is not None:
            logger.debug(f"Applying check {plugin.name} online.")
            result = self.execute_check_online(
                input_data, plugin, rego_file_path, self.config.opa_url
            )
        else:
            logger.debug(f"Applying check {plugin.name} in subprocess.")
            result = self.execute_check_in_subproc(input_data, plugin, rego_file_path)

        # format results
        result = plugin.plugin_obj.report_findings(result)
        return result

    @logger.catch(reraise=True)
    def _double_check_opa_existence(self, base_url: str | None) -> None:
        """Check if OPA is reachable.

        Raises:
            RuntimeError: If OPA is not reachable.
        """
        ver: str

        # fix slash issues and create base URL
        base_url = base_url.rstrip("/") if base_url is not None else None
        if base_url is not None:
            base_url = base_url + "/"

        if base_url is None:  # check for subproccess existence
            try:
                subprocess.run(
                    ["opa", "version"],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                ver = "subprocess"
            except Exception as e:
                logger.exception(e)
                raise RuntimeError("OPA subprocess not found or not installed!") from e
        else:  # check for online existence
            try:
                response = requests.get(base_url, timeout=default_timeout)
                if response.status_code == 200:
                    ver = "server"
                else:
                    raise RuntimeError(f"OPA server {base_url} not found or reachable!")
            except Exception as e:
                logger.exception(e)
                raise RuntimeError(
                    f"OPA server {base_url} not found or reachable!"
                ) from e

        logger.debug(f"OPA {ver} found and reachable!")

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
                    print(match.group(1))
                    return match.group(1)
        raise ValueError(f"Package name not found in {file_path}")

    @contextmanager
    @logger.catch(reraise=True)
    def _upload_temp_policy(self, plugin: PluginInfo, rego_path: Path, base_url: str):
        """Upload a policy to OPA server and remove it after use.

        Args:
            plugin (PluginInfo): The plugin to process.
            rego_path (Path): The path to the Rego file.
            base_url (str): The base URL of the OPA server.
        """
        info: RegoInfo = plugin.extra["rego"]

        # Extract package name from Rego file
        package_name = self._extract_package_name(rego_path)
        package_name_path = package_name.replace(".", "/")
        package_url = f"{base_url}/v1/policies/{package_name_path}"
        logger.debug(
            f"Uploading policy {info['rego_file']} with package name {package_name} to OPA server {base_url}"
        )

        # Upload policy to OPA server
        with open(rego_path, "r") as rego_file:
            policy_data = rego_file.read()
            resp = requests.put(
                package_url,
                data=policy_data,
                headers={"Content-Type": "text/plain"},
                timeout=default_timeout,
            )

            # check for success
            logger.trace(f"Policy Upload Code: {resp.status_code}")
            if resp.status_code != 200:
                logger.error(f"Policy upload failed: {resp.text}")
                raise RuntimeError(f"Policy upload failed: {resp.text}")
            else:
                logger.success(f"Policy {info['rego_file']} uploaded successfully.")

        # allow checks to run
        yield

        # Remove policy from OPA server
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

    def execute_check_in_subproc(
        self, data: "Result", plugin: PluginInfo, rego_file_path: str
    ) -> list["Result"]:
        """Applies a set of registered checks to the given data using the Open Policy Agent (OPA) CLI.

        Args:
            data (Result): The data to apply the checks to.
            plugin (PluginInfo): The plugin to apply the checks from.
            rego_file_path (str): The path to the Rego file.

        Returns:
            list[Result]: The results of the checks.
        """
        check: RegoInfo = plugin.extra["rego"]

        # Prepare data and command for OPA eval
        data = data.details
        temp_input_file_path = None
        try:
            # Write the input JSON to a temporary file in text mode
            with tempfile.NamedTemporaryFile(
                delete=False, mode="w", suffix=".json", encoding="utf-8"
            ) as temp_input_file:
                json.dump(
                    data["input"], temp_input_file
                )  # dump the input data to the temp file
                temp_input_file_path = temp_input_file.name

            # Prepare the OPA eval command
            package_name = self._extract_package_name(rego_file_path)
            opa_eval_command = [
                "opa",
                "eval",
                f"data.{package_name}",  # Adjust the query
                "--data",
                str(rego_file_path),
                "--input",
                str(temp_input_file_path),
                "--format=json",  # Add pretty format for debugging if needed
            ]

            # Debugging the command
            logger.debug(f"Running OPA command: {' '.join(opa_eval_command)}")

            # Run the OPA eval command
            process = subprocess.run(
                opa_eval_command, text=True, capture_output=True, check=True
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
            raise e

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OPA eval output: {e}")
            decision = {}
            result_details = []
            raise e

        except Exception as e:
            logger.error(f"Error running OPA eval: {e}")
            decision = {}
            result_details = []
            raise e

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

    def execute_check_online(
        self,
        data: "Result",
        plugin: "PluginInfo",
        rego_file_path: str,
        base_url: str,
        default_timeout: int = 20,
    ) -> list["Result"]:
        """Applies a set of registered checks to the given data using Open Policy Agent (OPA) server.

        Args:
            data (Result): The data to apply the checks to.
            plugin (PluginInfo): The plugin to apply the checks from.
            rego_file_path (str): The path to the Rego file.
            base_url (str): The base URL of the OPA server
            default_timeout (int): The default timeout for the request.

        Returns:
            list[Result]: The results of the checks.
        """
        with self._upload_temp_policy(
            plugin, rego_file_path, base_url
        ) as _:  # upload policy to OPA server
            # get plugin manifest info
            check: RegoInfo = plugin.extra["rego"]

            data = data.details

            # generate OPA URL
            package_name = self._extract_package_name(rego_file_path)
            package_name_path = package_name.replace(".", "/")
            opa_url = f"{base_url}/v1/data/{package_name_path}"

            # Query OPA server
            response = requests.post(opa_url, json=data, timeout=default_timeout)
            response_data = response.json()

            # Log Results
            logger.debug(f"OPA URL: {opa_url}")
            logger.debug(f"OPA response status code: {response.status_code}")
            if response.status_code != 200:
                logger.error(f"OPA response: {response_data}")
            else:
                logger.success(
                    f"OPA successfully queried for check {check['rego_file']}."
                )

            decision = response_data.get("result", False)
            result_details = (
                decision.get("details", []) if isinstance(decision, dict) else []
            )
            logger.success(decision)
            result = Result(
                relates_to=plugin.name,
                result_name=plugin.name,
                result_description=check["description"],
                details=result_details,
                formatted="",  # This will be filled in later
            )

            return result
