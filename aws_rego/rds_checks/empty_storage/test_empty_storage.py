import json
import os
import pathlib
from .empty_storage.empty_storage import EmptyStorage

# ruff: noqa: S101
def test_empty_storage(test_input_plugin):
    """Test for empty storage policy"""
    # Load rego policy
    current_dir = pathlib.Path(os.path.abspath(__file__)).parent

    # if test key does not exist in the result, the test will fail.
    # we need to add rds_empty_storage_threshold to the json file.
    write: bool = False
    test_data = os.path.join(current_dir.parent, "rds_test_data.json")
    with open(test_data, "r") as file:
        data = json.load(file)
        if "rds_empty_storage_threshold" not in data:
            data["rds_empty_storage_threshold"] = 50
            write = True

    # overwrite the file
    if write:
        with open(test_data, "w") as file:
            json.dump(data, file, indent=4)

    test_data_path = os.path.join(current_dir.parent, "rds_test_data.json")

    needed_keys = [
        "AllocatedStorage",
        "CPUUtilization",
        "Connections",
        "Engine",
        "InstanceIdentifier",
        "InstanceType",
        "Region",
        "StorageUtilization",
    ]

    result = test_input_plugin(test_data_path, EmptyStorage).details

    for item in result:
        for key in needed_keys:
            assert key in item, f"Key {key} not found in item {item}"
