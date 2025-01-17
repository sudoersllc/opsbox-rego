import os
import pathlib

def test_scaling_down(rego_process):
    current_dir = pathlib.Path(os.path.abspath(__file__)).parent
    rego_policy = os.path.join(current_dir, "scaling_down.rego")
    rego_input = os.path.join(current_dir.parent.parent, "rds_test_data.json")

    needed_keys = [
        "AllocatedStorage",
        "CPUUtilization",
        "Connections",
        "Engine",
        "InstanceIdentifier",
        "InstanceType",
        "Region",
        "StorageUtilization"
    ]

    result = rego_process(rego_policy, rego_input, "data.aws.cost.scaling_down", ["recommendations_for_scaling_down"])
    # check that result has the needed keys
    for key in needed_keys:
        assert key in result["recommendations_for_scaling_down"][0]