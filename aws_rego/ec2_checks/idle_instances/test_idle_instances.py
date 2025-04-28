import json
import os
import pathlib
from .idle_instances.idle_instances import IdleInstances


def test_idle_instances(test_input_plugin):
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

    test_data_path = os.path.join(current_dir.parent, "ec2_test_data.json")
    needed_keys = [
        "avg_cpu_utilization",
        "ebs_optimized",
        "instance_type",
        "operating_system",
        "processor",
        "region",
        "state",
        "tags",
        "tenancy",
        "virtualization_type",
    ]

    result = test_input_plugin(test_data_path, IdleInstances)
    for item in result.details:
        info = item[next(iter(item))]
        for key in needed_keys:
            assert key in info, f"Key {key} not found in {info}"
