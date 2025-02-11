import json
import os
import pathlib


def test_scaling_down(rego_process):
    current_dir = pathlib.Path(os.path.abspath(__file__)).parent

    # if test key does not exist in the result, the test will fail.
    # we need to add rds_cpu_scaling_threshold to the json file.
    write: bool = False
    test_data = os.path.join(current_dir.parent, "rds_test_data.json")
    with open(test_data, "r") as file:
        data = json.load(file)
        if "rds_cpu_scaling_threshold" not in data:
            data["rds_cpu_scaling_threshold"] = 20
            write = True

    # overwrite the file
    if write:
        with open(test_data, "w") as file:
            json.dump(data, file, indent=4)

    rego_policy = os.path.join(current_dir, "scaling_down.rego")
    rego_input = os.path.join(current_dir.parent, "rds_test_data.json")

    needed_keys = [
        "AllocatedStorage",
        "CPUUtilization",
        "Connections",
        "Engine",
        "InstanceIdentifier",
        "InstanceType",
        "Region",
        "StorageUtilization",
    ]

    result = rego_process(
        rego_policy,
        rego_input,
        "data.aws.cost.scaling_down",
        ["recommendations_for_scaling_down"],
    )
    # check that result has the needed keys
    for key in needed_keys:
        assert key in result["recommendations_for_scaling_down"][0]
