import json
import os
import pathlib
from .high_error_rate.high_error_rate import HighErrorRate


def test_high_error_rate(test_input_plugin):
    """Test for high error rates policy"""
    # Load rego policy
    current_dir = pathlib.Path(os.path.abspath(__file__)).parent

    # if test key does not exist in the result, the test will fail.
    # we need to add elb_error_rate_threshold to the json file.
    write: bool = False
    test_data = os.path.join(current_dir.parent, "elb_test_data.json")
    with open(test_data, "r") as file:
        data = json.load(file)
        if "elb_error_rate_threshold" not in data:
            data["elb_error_rate_threshold"] = 5
            write = True

    # overwrite the file
    if write:
        with open(test_data, "w") as file:
            json.dump(data, file, indent=4)

    # Load rego policy
    test_data_path = os.path.join(current_dir.parent, "elb_test_data.json")
    needed_keys = [
        "AvailabilityZones",
        "CreatedTime",
        "DNSName",
        "ErrorRate",
        "InstanceHealth",
        "Name",
        "RequestCount",
        "Scheme",
        "SecurityGroups",
        "Type",
    ]

    result = test_input_plugin(test_data_path, HighErrorRate)

    result = result.details

    for instance in result:
        for key in needed_keys:
            assert key in instance, f"Key {key} not found in {instance}"
    
