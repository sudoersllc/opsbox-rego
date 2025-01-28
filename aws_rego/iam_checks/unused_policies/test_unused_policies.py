import json
import os
import pathlib


# ruff: noqa: S101
def test_unused_policies(rego_process):
    """Test for unused policies policy"""
    # Load rego policy
    current_dir = pathlib.Path(os.path.abspath(__file__)).parent

    # if test key does not exist in the result, the test will fail.
    # we need to add iam_unused_attachment_threshold to the json file.
    write: bool = False
    test_data = os.path.join(current_dir.parent, "iam_test_data.json")
    with open(test_data, "r") as file:
        data = json.load(file)
        if "iam_unused_attachment_threshold" not in data:
            data["iam_unused_attachment_threshold"] = 0
            write = True

    # overwrite the file
    if write:
        with open(test_data, "w") as file:
            json.dump(data, file, indent=4)

    rego_policy = os.path.join(current_dir, "unused_policies.rego")
    rego_input = os.path.join(current_dir.parent, "iam_test_data.json")

    needed_keys = ["arn", "attachment_count", "create_date", "policy_id", "policy_name"]
    rego_process(rego_policy, rego_input, "data.aws.cost.unused_policies", needed_keys)
