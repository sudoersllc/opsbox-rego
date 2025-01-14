import os
import pathlib


# ruff: noqa: S101
def test_low_request_counts(rego_process):
    """Test for low request count policy"""
    # Load rego policy
    current_dir = pathlib.Path(os.path.abspath(__file__)).parent

    rego_policy = os.path.join(current_dir, "low_request_count.rego")
    rego_input = os.path.join(current_dir.parent.parent, "elb_test_data.json")

    needed_keys = ["AvailabilityZones", "CreatedTime", "DNSName", "ErrorRate", "InstanceHealth", "Name", "RequestCount", "Scheme", "SecurityGroups", "Type"]
    rego_process(rego_policy, rego_input, "data.aws.cost.low_request_count", needed_keys)

