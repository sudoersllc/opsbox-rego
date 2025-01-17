import os
import re
import json
import time
import pytest
import requests
import subprocess
from loguru import logger

# ruff: noqa: S607, S603, S101

default_timeout = 20

def _download_opa():
    """
    Helper function to download the OPA binary if missing.
    """
    if os.path.exists("./opa") or os.path.exists("./opa.exe"):
        logger.info("OPA already exists locally; not downloading again.")
        return

    logger.info(f"OS: {os.name}")
    logger.info(f"Downloading OPA to {os.getcwd()}")
    if os.name == "posix":
        subprocess.run(
            ["curl", "-L", "-o", "opa", "https://openpolicyagent.org/downloads/latest/opa_linux_amd64"],
            check=True
        )
        subprocess.run(["chmod", "755", "opa"], check=True)
    elif os.name == "nt":
        subprocess.run(
            ["curl", "-L", "-o", "opa.exe", "https://openpolicyagent.org/downloads/latest/opa_windows_amd64.exe"],
            check=True
        )
    elif os.name == "darwin":
        subprocess.run(
            ["curl", "-L", "-o", "opa", "https://openpolicyagent.org/downloads/latest/opa_darwin_amd64"],
            check=True
        )
        subprocess.run(["chmod", "755", "opa"], check=True)


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


@pytest.fixture(scope="module")
def rego_process():
    """
    This fixture:
    1. Downloads OPA if not present.
    2. Starts an OPA server on localhost:8181 (in a subprocess).
    3. Yields a function `_test_rego` which:
       - Uploads a Rego policy to the OPA server (PUT).
       - Sends input to OPA (POST) under the 'input' key.
       - Optionally checks certain keys in the result for your test validations.
       - Deletes the policy from OPA (cleanup).
    4. Terminates the OPA server after all tests in this session complete.
    5. Optionally removes the OPA binary from your working directory.
    """

    # 1) Download OPA if missing
    _download_opa()

    # 2) Start OPA server in a background subprocess on port 8181
    logger.info("Starting OPA server on :8181 ...")
    opa_cmd = ["./opa" if os.name != "nt" else "opa.exe", "run", "--server", "--addr", ":8181"]
    opa_server = subprocess.Popen(
        opa_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Give it a moment to spin up
    time.sleep(1)

    # 3) Provide test function that uses the running OPA server
    def _test_rego(rego_policy: str, rego_input: str, query: str = None, keys_to_check=None):
        """
        Uploads the Rego policy -> queries OPA with { "input": <the input> } -> 
        verifies keys -> cleans up by deleting the policy.

        Args:
            rego_policy (str): Path to .rego file.
            rego_input (str): Path to input JSON file.
            query (str, optional): If you want to query a subpath of the package.
                                   e.g. package = 'aws_rego.ec2_checks.ec2_old_snapshots'
                                   query might be 'ec2_old_snapshots' => /v1/data/aws_rego.ec2_checks.ec2_old_snapshots/ec2_old_snapshots
            keys_to_check (list, optional): A list of top-level keys you want to confirm in the returned dictionary.

        Returns:
            dict: The dictionary from OPA's /v1/data/<package>[/<query>] => result["result"] (or {} if not present).
        """
        # Read the Rego policy
        package_name = _extract_package_name(rego_policy)
        logger.info(f"Detected package name: {package_name}")
        package_path = package_name.replace(".", "/")

        with open(rego_policy, "r") as f:
            policy_code = f.read()

        # PUT /v1/policies/<package_path>
        put_url = f"http://localhost:8181/v1/policies/{package_path}"
        put_resp = requests.put(
            put_url,
            data=policy_code,
            headers={"Content-Type": "text/plain"},
            timeout=default_timeout
        )
        if put_resp.status_code != 200:
            logger.error(f"Failed to upload policy: {put_resp.text}")
            raise RuntimeError(f"Policy upload failed: status {put_resp.status_code}")
        logger.info("Policy uploaded successfully.")

        # Build the data URL for POST
        # e.g. /v1/data/aws_rego/ec2_checks/ec2_old_snapshots/<query>?
        data_url = f"http://localhost:8181/v1/data/{package_path}"

        # Load the JSON input file
        with open(rego_input, "r") as infile:
            input_data = json.load(infile)

        # POST the input as { "input": { ... } }
        logger.info(f"POSTing to {data_url} with input.")
        post_resp = requests.post(
            data_url,
            json={"input": input_data},  # <-- We nest the user data under "input".
            timeout=default_timeout
        )
        logger.info(f"Query status code: {post_resp.status_code}")
        if post_resp.status_code != 200:
            logger.error(f"Failed to query OPA: {post_resp.text}")
            raise RuntimeError(f"Policy query failed: status {post_resp.status_code}")

        # OPA typically responds with {"result": ...}
        response_json = post_resp.json()
        logger.debug(f"OPA response JSON: {json.dumps(response_json, indent=2)}")
        result = response_json.get("result", {})['details']

        # Optionally check for certain top-level keys
        if keys_to_check:
            for key in keys_to_check:
                if isinstance(result, dict) and key not in result:
                    msg = f"Key '{key}' not found in OPA details: {list(result.keys())}"
                    logger.error(msg)
                    raise AssertionError(msg)
                elif isinstance(result, list) and not all(key in x for x in result) or len(result) == 0:
                    msg = f"Key '{key}' not found in OPA details: {result}"
                    logger.error(msg)
                    raise AssertionError(msg)

        # Delete policy from OPA as cleanup
        del_resp = requests.delete(put_url, timeout=default_timeout)
        if del_resp.status_code != 200:
            logger.warning(f"Failed to delete policy: {del_resp.text}")
        else:
            logger.info("Policy removed from OPA successfully.")

        # Return the entire decision dictionary
        return result

    # Hand off our helper function to the test
    yield _test_rego

    # 4) Teardown: stop the OPA server
    logger.info("Stopping OPA server...")
    opa_server.terminate()
    try:
        opa_server.wait(timeout=5)
    except subprocess.TimeoutExpired:
        logger.warning("OPA server did not stop gracefully; killing it.")
        opa_server.kill()

    # 5) Optionally remove the OPA binary
    # Comment out if you prefer to keep it for debugging/future runs
    logger.info(f"Cleaning up OPA binary from {os.getcwd()}")
    if os.name == "posix":
        try:
            os.remove(os.path.join(os.getcwd(), "opa"))
        except FileNotFoundError:
            pass
    elif os.name == "nt":
        try:
            os.remove(os.path.join(os.getcwd(), "opa.exe"))
        except FileNotFoundError:
            pass
    elif os.name == "darwin":
        try:
            os.remove(os.path.join(os.getcwd(), "opa"))
        except FileNotFoundError:
            pass
