import json
import os
import pathlib
from .low_request_count import LowRequestCount


def test_low_request_counts(test_input_plugin):
    """Test for low request counts policy"""
    current_dir = pathlib.Path(os.path.abspath(__file__)).parent

    # if test key does not exist in the result, the test will fail.
    # we need to add elb_request_count_threshold to the json file.
    write: bool = False
    test_data = os.path.join(current_dir.parent, "elb_test_data.json")
    with open(test_data, "r") as file:
        data = json.load(file)
        if "elb_request_count_threshold" not in data:
            data["elb_request_count_threshold"] = 100
            write = True

    # overwrite the file
    if write:
        with open(test_data, "w") as file:
            json.dump(data, file, indent=4)

    test_data_path = os.path.join(current_dir.parent, "elb_test_data.json")
    needed_keys = [
        "CreatedTime",
        "DNSName",
        "RequestCount",
        "InstanceHealth",
        "Name",
        "Scheme",
        "SecurityGroups",
        "Type",
    ]

    result = test_input_plugin(test_data_path, LowRequestCount)
    # check that result has the needed keys
    details = result.details

    for instance in details:
        for key in needed_keys:
            assert key in instance
