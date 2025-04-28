import json
import os
import pathlib
from .scaling_down.scaling_down import ScalingDown

def test_scaling_down(test_input_plugin):
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

    test_data_path = os.path.join(current_dir.parent, "rds_test_data.json")

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

    result = test_input_plugin(test_data_path, ScalingDown)
    # check that result has the needed keys
    details = result.details
    for key in needed_keys:
        assert key in details["recommendations_for_scaling_down"][0]
