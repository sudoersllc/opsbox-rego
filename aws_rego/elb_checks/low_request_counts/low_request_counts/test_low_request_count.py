import json
import os
import pathlib


# ruff: noqa: S101
def test_low_request_counts(rego_process):
    """Test for low request count policy"""
    # Load rego policy
    current_dir = pathlib.Path(os.path.abspath(__file__)).parent

    # if test key does not exist in the result, the test will fail.
    # we need to add elb_low_requests_threshold to the json file.
    write: bool = False
    test_data = os.path.join(current_dir.parent.parent, "elb_test_data.json")
    with open(test_data, "r") as file:
        data = json.load(file)
        if "elb_low_requests_threshold" not in data:
            data["elb_low_requests_threshold"] = 50
            write = True

    # overwrite the file
    if write:
        with open(test_data, "w") as file:
            json.dump(data, file, indent=4)

    rego_policy = os.path.join(current_dir, "low_request_count.rego")
    rego_input = os.path.join(current_dir.parent.parent, "elb_test_data.json")

    needed_keys = ["AvailabilityZones", "CreatedTime", "DNSName", "ErrorRate", "InstanceHealth", "Name", "RequestCount", "Scheme", "SecurityGroups", "Type"]
    rego_process(rego_policy, rego_input, "data.aws.cost.low_request_count", needed_keys)

