# test_no_healthy_targets.py

import os
import pathlib


def test_no_healthy_targets(rego_process):
    current_dir = pathlib.Path(os.path.abspath(__file__)).parent
    rego_policy = os.path.join(current_dir, "no_healthy_targets.rego")
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

    result = rego_process(rego_policy, rego_input, "data.aws.elb.no_healthy_targets")
    # check that result has the needed keys
    for key in needed_keys:
        assert key in result[0]
