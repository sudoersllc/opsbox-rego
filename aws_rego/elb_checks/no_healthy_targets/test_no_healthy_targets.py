# test_no_healthy_targets.py

import os
import pathlib
from .no_healthy_targets.no_healthy_targets import NoHealthyTargets


def test_no_healthy_targets(test_input_plugin):
    current_dir = pathlib.Path(os.path.abspath(__file__)).parent
    test_data_path = os.path.join(current_dir.parent, "elb_test_data.json")

    needed_keys = [
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

    result = test_input_plugin(test_data_path, NoHealthyTargets)
    result = result.details

    # check that result has the needed keys
    for x in result:
        for key in needed_keys:
            assert key in x
