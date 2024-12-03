
import pytest
import os
import subprocess
import json
from loguru import logger
# ruff: noqa: S607, S603, S101

def _download_opa():
    """Helper function to download OPA binary.
    
    Will download the OPA binary based on the OS to root of the project."""
    if os.path.exists(".\opa") or os.path.exists(".\opa.exe"):
        logger.info("OPA already exists! Using it instead...")
    else:
        logger.info(f"OS: {os.name}")
        logger.info(f"Downloading OPA to {os.getcwd()}")
        if os.name == "posix":
            subprocess.run(["curl", "-L", "-o", "opa", "https://openpolicyagent.org/downloads/latest/opa_linux_amd64"], check=True)
            subprocess.run(["chmod", "755", "opa"], check=True)
        elif os.name == "nt":
            subprocess.run(["curl", "-L", "-o", "opa.exe", "https://openpolicyagent.org/downloads/latest/opa_windows_amd64.exe"], check=True)    
        elif os.name == "darwin":
            subprocess.run(["curl", "-L", "-o", "opa", "https://openpolicyagent.org/downloads/latest/opa_darwin_amd64"], check=True)
            subprocess.run(["chmod", "755", "opa"], check=True)


@pytest.fixture(scope="session")
def rego_process():
    """Fixture to test rego policies. Returns a function to test rego policies."""
    _download_opa()
    def _test_rego(rego_policy, rego_input, query, keys_to_check=None):
        """Function to test rego policies.
        
        Args:
            rego_policy (str): Path to rego policy file.
            rego_input (str): Path to rego input file.
            query (str): Query to run against the rego policy.
            keys_to_check (list, optional): List of keys to check in the result. Defaults to None.
        
        Returns:
            dict: Result of the rego policy.
        """
        logger.info(f"Running rego policy {rego_policy} with input {rego_input} and query {query}")

        item = subprocess.run(["opa", "eval","-d", rego_policy, "-i", rego_input, query], check=True, capture_output=True)  # noqa: S607

        output = json.loads(item.stdout.decode("utf-8"))
        logger.info(output)
        details = output["result"][0]["expressions"][0]["value"]["details"]
        if keys_to_check and type(details) is list:
            for item in details:
                for key in keys_to_check:
                    assert key in item, f"Key {key} not found in {item.keys()}"
        elif keys_to_check and type(details) is dict:
            for key in keys_to_check:
                assert key in details, f"Key {key} not found in {details.keys()}"
        return details
    
    yield _test_rego

    # Clean up
    path = os.getcwd()
    logger.info(f"Cleaning up OPA binary from {path}")
    if os.name == "posix":
        os.remove(os.path.join(path, "opa"))
    elif os.name == "nt":
        os.remove(os.path.join(path, "opa.exe"))
    elif os.name == "darwin": 
        os.remove(os.path.join(path, "opa"))