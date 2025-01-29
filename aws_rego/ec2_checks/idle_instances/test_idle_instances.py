import json
import os
import pathlib

def test_idle_instances(rego_process):
    """Test for idle instances rego policy"""
    # Load rego policy
    current_dir = pathlib.Path(os.path.abspath(__file__)).parent
    
    # if test key does not exist in the result, the test will fail.
    # we need to add ec2_cpu_idle_threshold to the json file.
    write: bool = False
    test_data = os.path.join(current_dir.parent, "ec2_test_data.json")
    with open(test_data, "r") as file:
        data = json.load(file)
        if "ec2_cpu_idle_threshold" not in data:
            data["ec2_cpu_idle_threshold"] = 1
            write = True

    # overwrite the file
    if write:
        with open(test_data, "w") as file:
            json.dump(data, file, indent=4)

    
    rego_policy = os.path.join(current_dir, "idle_instances.rego")
    rego_input = os.path.join(current_dir.parent, "ec2_test_data.json")
    needed_keys = ["avg_cpu_utilization", "ebs_optimized", "instance_id", "instance_type", "operating_system", "processor", "region", "state", "tags", "tenancy", "virtualization_type"]
    rego_process(rego_policy, rego_input, "aws_rego.ec2_checks.idle_instances.idle_instances", needed_keys)
