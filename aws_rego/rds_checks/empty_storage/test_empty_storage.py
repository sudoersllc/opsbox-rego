import os
import pathlib


# ruff: noqa: S101
def test_empty_storage(rego_process):
    """Test for empty storage policy"""
    # Load rego policy
    current_dir = pathlib.Path(os.path.abspath(__file__)).parent

    rego_policy = os.path.join(current_dir, "empty_storage.rego")
    rego_input = os.path.join(current_dir.parent, "rds_test_data.json")

    result = rego_process(rego_policy, rego_input, "data.aws.cost.empty_storage", ["empty_storage_instances"])
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
    for x in result["empty_storage_instances"]:
        for key in needed_keys:
            assert key in x, f"Key {key} not found in {x}"
