import json
import os
import pathlib


def test_high_error_rate(rego_process):
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
    rego_policy = os.path.join(current_dir, "high_error_rate.rego")
    rego_input = os.path.join(current_dir.parent, "elb_test_data.json")
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
        "State",
        "Type",
        "VpcId",
    ]
    rego_process(rego_policy, rego_input, "data.aws.cost.high_error_rate", needed_keys)
