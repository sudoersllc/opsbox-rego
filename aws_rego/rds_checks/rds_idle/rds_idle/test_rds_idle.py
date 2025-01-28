import json
import os
import pathlib


# ruff: noqa: S101
def test_rds_idle(rego_process):
    """Test for rds idle policy"""
    # Load rego policy
    current_dir = pathlib.Path(os.path.abspath(__file__)).parent

    # if test key does not exist in the result, the test will fail.
    # we need to add rds_cpu_idle_threshold to the json file.
    write: bool = False
    test_data = os.path.join(current_dir.parent.parent, "rds_test_data.json")
    with open(test_data, "r") as file:
        data = json.load(file)
        if "rds_cpu_idle_threshold" not in data:
            data["rds_cpu_idle_threshold"] = 5
            write = True

    # overwrite the file
    if write:
        with open(test_data, "w") as file:
            json.dump(data, file, indent=4)
            
    rego_policy = os.path.join(current_dir, "rds_idle.rego")
    rego_input = os.path.join(current_dir.parent.parent, "rds_test_data.json")

    needed_keys = [
        "AllocatedStorage",
        "CPUUtilization",
        "Connections",
        "Engine",
        "InstanceIdentifier",
        "InstanceType",
        "Region",
        "StorageUtilization"
    ]
    rego_process(rego_policy, rego_input, "data.aws.cost.rds_idle", needed_keys)
