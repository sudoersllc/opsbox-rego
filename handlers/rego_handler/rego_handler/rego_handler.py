import contextlib
import hashlib
from pathlib import Path
import platform
from pydantic import BaseModel, Field
import requests
from opsbox import PluginInfo, Registry, Result
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

        if self.config.opa_url is not None:
            self.config.opa_url = self.config.opa_url.rstrip("/")
            self.exec_obj = ExecOnline()
            self.exec_obj.check_opa_existence(self.config.opa_url)
        else:
            self.exec_obj = ExecLocal()
            self.exec_obj.check_opa_existence(None)

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
            for x in registry.active_plugins
            if (x.type == "provider") and (x.name in plugin.uses)
        ]

        if len(providers) == 1:
            logger.trace(f"Provider found for rego plugin {plugin.name}.")
            provider = providers[0]
            input_data = provider.plugin_obj.gather_data()
            logger.debug(f"Input provider data gathered for plugin {plugin.name}.")
        if len(providers) > 1:
            raise RuntimeError("Rego plugins can only use one provider.")
        if len(providers) == 0:
            logger.warning(
                f"No provider found for rego plugin {plugin.name}. Using prior results."
            )

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
            logger.debug(
                f"Data injected for plugin {plugin.name}.",
                extra={"after_inject": input_data},
            )
        # apply check
        result = self.exec_obj.execute_check(input_data, plugin, rego_file_path)

        # format results
        result = plugin.plugin_obj.report_findings(result)
        return result


def extract_package_name(file_path):
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


class RegoExecution:
    """An Abstract Base Class for executing Rego checks."""

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

        with open(file_path, "r") as file:
            # Find the first line matching the package pattern
            for line in file:
                match = package_pattern.match(line.strip())
                if match:
                    return match.group(1)
        raise ValueError(f"Package name not found in {file_path}")

    def check_opa_existence(self, base_url: str | None) -> None:
        """Check if OPA is reachable.

        Raises:
            RuntimeError: If OPA is not reachable.
        """
        raise NotImplementedError()

    def execute_check(
        self, data: "Result", plugin: "PluginInfo", rego_file_path: str
    ) -> list["Result"]:
        """Applies a registered check to the given data using the Open Policy Agent (OPA).

        Args:
            data (Result): The data to apply the check to.
            plugin (PluginInfo): The plugin to apply the check from.
            rego_file_path (str): The path to the Rego file.

        Returns:
            list[Result]: The results of the check.
        """
        raise NotImplementedError()


class ExecOnline(RegoExecution):
    """A class for executing Rego checks using an online OPA server.

    Attributes:
        base_url (str): The base URL of the OPA server."""

    def check_opa_existence(self, base_url: str) -> None:
        """Check if OPA is reachable online.

        Raises:
            RuntimeError: If OPA is not reachable.
        """

        # check for online existence
        try:
            response = requests.get(base_url, timeout=default_timeout)
            if not response.status_code == 200:
                raise RuntimeError(f"OPA server {base_url} not found or reachable!")
            else:
                self.base_url = base_url
        except Exception as e:
            logger.exception(e)
            raise RuntimeError(f"OPA server {base_url} not found or reachable!") from e

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
        package_name = extract_package_name(rego_path)
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

            logger.trace(
                f"Policy {info['rego_file']} uploaded to OPA server {base_url} with response code {resp.status_code}"
            )

            # check for success
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
            logger.success(
                f"Policy {info['rego_file']} removed from the server successfully."
            )

    def execute_check(
        self, data: "Result", plugin: "PluginInfo", rego_file_path: str
    ) -> list["Result"]:
        """Applies a registered check to the given data using the Open Policy Agent (OPA) server.

        Args:
            data (Result): The data to apply the check to.
            plugin (PluginInfo): The plugin to apply the check from.
            rego_file_path (str): The path to the Rego file.

        Returns:
            list[Result]: The results of the check.
        """
        logger.info(
            f"Applying check {plugin.name} using OPA server located at {self.base_url}."
        )
        with self._upload_temp_policy(
            plugin, rego_file_path, self.base_url
        ) as _:  # upload policy to OPA server
            # get plugin manifest info
            check: RegoInfo = plugin.extra["rego"]

            data = data.details

            # generate OPA URL
            package_name = extract_package_name(rego_file_path)
            package_name_path = package_name.replace(".", "/")
            opa_url = f"{self.base_url}/v1/data/{package_name_path}"

            # Query OPA server
            response = requests.post(opa_url, json=data, timeout=default_timeout)
            response_data = response.json()

            # Log Results
            logger.trace(
                f"OPA response from post to {opa_url} returned code {response.status_code}"
            )

            if response.status_code != 200:
                logger.error(
                    f"OPA server did not return a 200 status code, instead it returned {response.status_code}.",
                    extra={"response": response_data},
                )
            else:
                logger.success(
                    f"OPA successfully queried for check {check['rego_file']}.",
                    extra={"response": response_data},
                )

            # format to result
            decision = response_data.get("result", False)
            result_details = (
                decision.get("details", []) if isinstance(decision, dict) else []
            )
            result = Result(
                relates_to=plugin.name,
                result_name=plugin.name,
                result_description=check["description"],
                details=result_details,
                formatted="",  # This will be filled in later
            )

            return result


class ExecLocal(RegoExecution):
    """A class for executing Rego checks using the OPA CLI.

    Attributes:
        opa_fp (Path): The path to the OPA binary."""

    def check_opa_existence(self, base_url: None) -> None:
        """Check if OPA is reachable locally.

        Raises:
            RuntimeError: If OPA is not reachable.
        """

        # check if we need to download OPA
        current_dir = Path(__file__).parent
        if "opa" in os.listdir(current_dir) or "opa.exe" in os.listdir(current_dir):
            logger.debug("OPA binary already exists in the current directory.")
            if platform.system().lower() != "windows":
                self.opa_fp = current_dir / "opa"
            else:
                self.opa_fp = current_dir / "opa.exe"
            return
        else:
            logger.info("Downloading OPA binary to the file directory.")

        # we want to fix to a specific version
        base_url = "https://openpolicyagent.org/downloads/v1.1.0"

        # case using user's OS
        platform_tuple = (platform.system().lower(), platform.machine().lower())
        logger.trace(f"User's platform: {platform_tuple}")
        match (platform.system().lower(), platform.machine().lower()):
            case ("linux", "amd64") | ("linux", "x86_64"):
                url = f"{base_url}/opa_linux_amd64_static"
            case ("linux", "aarch64"):
                url = f"{base_url}/opa_linux_arm64_static"
            case ("darwin", "arm64"):
                url = f"{base_url}/opa_darwin_arm64_static"
            case ("darwin", "amd64") | ("darwin", "x86_64"):
                url = f"{base_url}/opa_darwin_amd64_static"
            case ("windows", "amd64") | ("windows", "x86_64"):
                url = f"{base_url}/opa_windows_amd64.exe"
            case _:
                raise RuntimeError("OS or architecture not supported by OPA.")

        checksum_url = f"{url}.sha256"

        # download the checksum
        checksum_fp = current_dir / "opa.sha256"
        with requests.get(checksum_url, stream=True) as r:
            r.raise_for_status()
            with open(checksum_fp, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        # download the binary
        if platform.system().lower() != "windows":
            binary_fp = current_dir / "opa"
        else:
            binary_fp = current_dir / "opa.exe"

        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(binary_fp, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        # check the checksum
        with open(checksum_fp, "r") as f:
            checksum = f.read().split()[0]
        with open(binary_fp, "rb") as f:
            binary = f.read()
        if hashlib.sha256(binary).hexdigest() != checksum:
            raise RuntimeError("Checksum does not match.")

        # make the binary executable
        if platform.system().lower() != "windows":
            os.chmod(binary_fp, 0o755)

        # check for subproccess existence
        try:
            subprocess.run(
                [str(binary_fp), "version"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception as e:
            logger.exception(e)
            raise RuntimeError("OPA subprocess not found or not installed!") from e

    def execute_check(
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
            package_name = extract_package_name(rego_file_path)
            opa_eval_command = [
                str(self.opa_fp),
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

            logger.success(
                f"OPA eval successfully executed for {check['rego_file']}.",
                extra={"result": decision},
            )

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
