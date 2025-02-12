import os
import pathlib


def test_idle_instances(rego_process):
    """Test for idle instances rego policy"""
    # Load rego policy
    current_dir = pathlib.Path(os.path.abspath(__file__)).parent

    rego_policy = os.path.join(current_dir, "stray_ebs.rego")
    rego_input = os.path.join(current_dir.parent, "ec2_test_data.json")
    needed_keys = ["create_time", "region", "size", "state", "tags", "volume_id"]
    rego_process(
        rego_policy, rego_input, "aws_rego.ec2_checks.stray_ebs.stray_ebs", needed_keys
    )
