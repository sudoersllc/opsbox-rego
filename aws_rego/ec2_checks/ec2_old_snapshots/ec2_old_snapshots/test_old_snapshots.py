import os
import pathlib

# ruff: noqa: S101

def test_idle_instances(rego_process):
    """Test for idle instances rego policy"""
    # Load rego policy
    current_dir = pathlib.Path(os.path.abspath(__file__)).parent

    rego_policy = os.path.join(current_dir, "ec2_old_snapshots.rego")
    rego_input = os.path.join(current_dir.parent.parent, "ec2_test_data.json")

    needed_keys = ["progress", "region", "snapshot_id", "start_time", "state", "tags", "volume_id"]
    result = rego_process(rego_policy, rego_input, "aws_rego.ec2_checks.ec2_old_snapshots.ec2_old_snapshots", ["ec2_old_snapshots"])

    for x in result["ec2_old_snapshots"]:
        for key in needed_keys:
            assert key in x, f"Key {key} not found in {x}"  
