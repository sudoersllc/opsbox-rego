import os
import pathlib


def test_high_error_rate(rego_process):
    """Test for high error rates policy"""
    # Load rego policy
    current_dir = pathlib.Path(os.path.abspath(__file__)).parent

    rego_policy = os.path.join(current_dir, "high_error_rate.rego")
    rego_input = os.path.join(current_dir.parent, "elb_test_data.json")
    needed_keys = ["AvailabilityZones", "CreatedTime", "DNSName", "ErrorRate", "InstanceHealth", "Name", "RequestCount", "Scheme", "SecurityGroups", "State", "Type", "VpcId"]
    rego_process(rego_policy, rego_input, "data.aws.cost.high_error_rate", needed_keys)
