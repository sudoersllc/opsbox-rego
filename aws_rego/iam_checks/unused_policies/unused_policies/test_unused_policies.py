import os
import pathlib


# ruff: noqa: S101
def test_unused_policies(rego_process):
    """Test for unused policies policy"""
    # Load rego policy
    current_dir = pathlib.Path(os.path.abspath(__file__)).parent

    rego_policy = os.path.join(current_dir, "unused_policies.rego")
    rego_input = os.path.join(current_dir.parent.parent, "iam_test_data.json")

    needed_keys = ["arn", "attachment_count", "create_date", "policy_id", "policy_name"]
    rego_process(rego_policy, rego_input, "data.aws.cost.unused_policies", needed_keys)
