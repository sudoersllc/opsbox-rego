import os
import pathlib

def test_idle_instances(rego_process):
    """Test for idle instances rego policy"""
    # Load rego policy
    current_dir = pathlib.Path(os.path.abspath(__file__)).parent

    rego_policy = os.path.join(current_dir, "idle_instances.rego")
    rego_input = os.path.join(current_dir.parent, "ec2_test_data.json")
    needed_keys = ["avg_cpu_utilization", "ebs_optimized", "instance_id", "instance_type", "operating_system", "processor", "region", "state", "tags", "tenancy", "virtualization_type"]
    rego_process(rego_policy, rego_input, "data.aws.cost.idle_instances", needed_keys)
