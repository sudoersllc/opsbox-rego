import os
import pathlib


# ruff: noqa: S101
def test_unused_buckets(rego_process):
    """Test for unused buckets policy"""
    # Load rego policy
    current_dir = pathlib.Path(os.path.abspath(__file__)).parent

    rego_policy = os.path.join(current_dir, "unused_buckets.rego")
    rego_input = os.path.join(current_dir.parent, "s3_test_data.json")

    needed_keys = ["last_modified", "name", "storage_class"]
    result = rego_process(rego_policy, rego_input, "data.aws.cost.unused_buckets", ["unused_buckets"])
    for x in result["unused_buckets"]:
        for key in needed_keys:
            assert key in x, f"Key {key} not found in {x}"
