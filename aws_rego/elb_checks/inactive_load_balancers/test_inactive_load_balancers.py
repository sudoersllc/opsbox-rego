import json
import os
import pathlib
from .inactive_load_balancers.inactive_load_balancers import InactiveLoadBalancers


def test_inactive_load_balancers(test_input_plugin):
    """Test for inactive load balancers"""
    current_dir = pathlib.Path(os.path.abspath(__file__)).parent

    # if test key does not exist in the result, the test will fail.
    # we need to add elb_inactive_requests_threshold to the json file.
    write: bool = False
    test_data = os.path.join(current_dir.parent, "elb_test_data.json")
    with open(test_data, "r") as file:
        data = json.load(file)
        if "elb_inactive_requests_threshold" not in data:
            data["elb_inactive_requests_threshold"] = 0
            write = True

    # overwrite the file
    if write:
        with open(test_data, "w") as file:
            json.dump(data, file, indent=4)

    rego_input = os.path.join(current_dir.parent, "elb_test_data.json")
    needed_keys = [
        "CreatedTime",
        "DNSName",
        "InstanceHealth",
        "Name",
        "RequestCount",
        "Scheme",
        "SecurityGroups",
        "Type",
    ]

    result = test_input_plugin(rego_input, InactiveLoadBalancers)
    # check that result has the needed keys
    details = result.details

    for instance in details:
        for key in needed_keys:
            assert key in instance, f"{instance}"

