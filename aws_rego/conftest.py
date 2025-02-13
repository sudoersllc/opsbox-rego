import re
import json
import pytest
from loguru import logger
from regopy import Interpreter
# ruff: noqa: S607, S603, S101


def _extract_package_name(rego_policy_path: str) -> str:
    """
    Extracts the package name from the first line that matches `package xyz`.
    Returns something like 'aws_rego.ec2_checks.ec2_old_snapshots' if that's in the .rego.
    Used to build the /v1/policies/<package> and /v1/data/<package> endpoints.
    """
    package_pattern = re.compile(r"^package\s+([a-zA-Z0-9_.]+)")
    with open(rego_policy_path, "r") as rego_file:
        for line in rego_file:
            match = package_pattern.match(line.strip())
            if match:
                return match.group(1)
    raise ValueError(f"Package name not found in {rego_policy_path}")


def _test_rego_with_interpreter(rego_path: str, input_data: str, query: str, keys_to_check=None):
    """Function to test rego policies.
    Args:
        rego_path (str): Path to rego policy file.
        input_data (str): Path to rego input file.
        query (str): Query to run against the rego policy.
        keys_to_check (list, optional): List of keys to check in the result. Defaults to None.
    Returns:
        dict: Result of the rego policy's details.
    """
    logger.info(
        f"Running rego policy {rego_path} with input {input_data} and query {query}"
    )

    # get the package name from the rego file, used to build the query
    package_name = _extract_package_name(rego_path)
    query = f"data.{package_name}"

    interpreter = Interpreter() # set interpreter

    # load the rego policy
    with open(rego_path, "r") as rego_file:
        rego = rego_file.read()
        interpreter.add_module(package_name, rego)

    # load the input data
    with open(input_data, "r") as input_file:
        input_data = json.load(input_file)
        interpreter.set_input(input_data)

    # run the query
    result = interpreter.query(query)

    # grab the details from the result
    details = result[0][0]["details"]

    print(details)

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
    yield _test_rego_with_interpreter
