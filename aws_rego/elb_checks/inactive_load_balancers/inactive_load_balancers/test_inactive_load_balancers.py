import json
import os
import pathlib

def test_inactive_load_balancers(rego_process):
    current_dir = pathlib.Path(os.path.abspath(__file__)).parent

    # if test key does not exist in the result, the test will fail.
    # we need to add elb_inactive_requests_threshold to the json file.
    write: bool = False
    test_data = os.path.join(current_dir.parent.parent, "elb_test_data.json")
    with open(test_data, "r") as file:
        data = json.load(file)
        if "elb_inactive_requests_threshold" not in data:
            data["elb_inactive_requests_threshold"] = 0
            write = True

    # overwrite the file
    if write:
        with open(test_data, "w") as file:
            json.dump(data, file, indent=4)

    # Load rego policy
    rego_policy = os.path.join(current_dir, "inactive_load_balancers.rego")
    rego_input = os.path.join(current_dir.parent.parent, "elb_test_data.json")
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
        "VpcId"
    ]

    result = rego_process(rego_policy, rego_input, "data.aws.elb.inactive_load_balancers")
    # check that result has the needed keys
    for key in needed_keys:
        assert key in result[0]