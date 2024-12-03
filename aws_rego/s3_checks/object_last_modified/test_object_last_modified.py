import os
import pathlib


# ruff: noqa: S101
def test_object_last_modified(rego_process):
    """Test for object last modified policy"""
    # Load rego policy
    current_dir = pathlib.Path(os.path.abspath(__file__)).parent

    rego_policy = os.path.join(current_dir, "object_last_modified.rego")
    rego_input = os.path.join(current_dir.parent, "s3_test_data.json")

    needed_keys = ["percentage_standard_and_old","standard_and_old_objects", "total_objects"]
    rego_process(rego_policy, rego_input, "data.aws.cost.object_last_modified", needed_keys)

