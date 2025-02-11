import os
import pathlib


def test_unattached_eips(rego_process):
    """Test for idle instances rego policy"""
    # Load rego policy
    current_dir = pathlib.Path(os.path.abspath(__file__)).parent

    rego_policy = os.path.join(current_dir, "unattached_eips.rego")
    rego_input = os.path.join(current_dir.parent, "ec2_test_data.json")
    needed_keys = ["association_id", "domain", "public_ip", "region"]
    rego_process(rego_policy, rego_input, "data.aws.cost.unattached_eips", needed_keys)
