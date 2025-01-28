# test_rds_old_snapshots.py

import json
import os
import pathlib
from datetime import datetime, timedelta

def test_rds_old_snapshots(rego_process):
    current_dir = pathlib.Path(os.path.abspath(__file__)).parent
    rego_policy = os.path.join(current_dir, "rds_old_snapshots.rego")
    rego_input = os.path.join(current_dir.parent, "rds_test_data.json")

    # if test key does not exist in the result, the test will fail.
    # we need to add rds_old_date_threshold to the json file.
    write: bool = False
    test_data = os.path.join(current_dir.parent, "rds_test_data.json")
    with open(test_data, "r") as file:
        data = json.load(file)
        if "rds_old_date_threshold" not in data:
            data["rds_old_date_threshold"] = int((datetime.now() - timedelta(days=10)).timestamp() * 1e9)
            write = True

    # overwrite the file
    if write:
        with open(test_data, "w") as file:
            json.dump(data, file, indent=4)

    needed_keys = [
        "AllocatedStorage",
        "InstanceIdentifier",
        "SnapshotCreateTime",
        "SnapshotIdentifier",
        "StorageType"
    ]

    result = rego_process(rego_policy, rego_input, "data.aws.cost.rds_old_snapshots", ["rds_old_snapshots"])
    # check that result has the needed keys
    for key in needed_keys:
        assert key in result["rds_old_snapshots"][0]