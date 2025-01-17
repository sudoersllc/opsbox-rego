import os
import pathlib

def test_inactive_load_balancers(rego_process):
    current_dir = pathlib.Path(os.path.abspath(__file__)).parent
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