import os
import re
import json
import time
import pytest
import requests
import subprocess
from loguru import logger
# ruff: noqa: S607, S603, S101

def _extract_package_name(rego_policy_path: str) -> str:
    """
    Extracts the package name from the first line that matches `package xyz`.
    Returns something like 'aws_rego.ec2_checks.ec2_old_snapshots' if that's in the .rego.
    Used to build the /v1/policies/<package> and /v1/data/<package> endpoints.
    """
    package_pattern = re.compile(r"^package\s+([a-zA-Z0-9_.]+)")
    with open(rego_policy_path, 'r') as rego_file:
        for line in rego_file:
            match = package_pattern.match(line.strip())
            if match:
                return match.group(1)
    raise ValueError(f"Package name not found in {rego_policy_path}")

def _download_opa():
    """Helper function to download OPA binary based on the OS to the root of the project."""
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

def _clean_opa():
    """Helper function to remove OPA binary from the root of the project."""
    path = os.getcwd()
    logger.info(f"Cleaning up OPA binary from {path}")
    if os.name == "posix":
        os.remove(os.path.join(path, "opa"))
    elif os.name == "nt":
        os.remove(os.path.join(path, "opa.exe"))
    elif os.name == "darwin":
        os.remove(os.path.join(path, "opa"))

def _test_rego(rego_path: str, input_data: str, query: str, keys_to_check=None):
    """Function to test rego policies.
    Args:
        rego_path (str): Path to rego policy file.
        input_data (str): Path to rego input file.
        query (str): Query to run against the rego policy.
        keys_to_check (list, optional): List of keys to check in the result. Defaults to None.
    Returns:
        dict: Result of the rego policy's details.
    """
    logger.info(f"Running rego policy {rego_path} with input {input_data} and query {query}")

    package_name = _extract_package_name(rego_path)
    query = f"data.{package_name}"
    item = subprocess.run(["opa", "eval","-d", rego_path, "-i", input_data, query, "--format=json"], check=True, capture_output=True)  # noqa: S607
    output = json.loads(item.stdout.decode("utf-8"))
    logger.info(output)
    details = output["result"][0]["expressions"][0]["value"]["details"]
    
    # check if keys are present in the result list
    if keys_to_check and type(details) is list:
        for item in details:
            for key in keys_to_check:
                assert key in item, f"Key {key} not found in {item.keys()}"
    # check if keys are present in the result dict
    elif keys_to_check and type(details) is dict:
        for key in keys_to_check:
            assert key in details, f"Key {key} not found in {details.keys()}"
    return details


@pytest.fixture(scope="session")
def rego_process():
    """Fixture to test rego policies. Returns a function to test rego policies."""
    _download_opa()
    yield _test_rego
    _clean_opa()