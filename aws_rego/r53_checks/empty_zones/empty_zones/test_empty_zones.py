import os
import pathlib


# ruff: noqa: S101
def test_unused_policies(rego_process):
    """Test for unused policies policy"""
    # Load rego policy
    current_dir = pathlib.Path(os.path.abspath(__file__)).parent

    rego_policy = os.path.join(current_dir, "empty_zones.rego")
    rego_input = os.path.join(current_dir.parent.parent, "r53_test_data.json")

    needed_keys = ["id", "name", "private_zone", "record_count"]
    result = rego_process(rego_policy, rego_input, "data.aws.cost.unused_policies", ["empty_hosted_zones"])
    for key in needed_keys:
        assert key in result["empty_hosted_zones"][0]
