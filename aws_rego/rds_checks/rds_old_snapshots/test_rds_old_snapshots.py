# test_rds_old_snapshots.py

import json
import os
import pathlib
from datetime import datetime, timedelta
from opsbox import Result
from .rds_old_snapshots.rds_old_snapshots import RDSOldSnapshots


def test_rds_old_snapshots(test_input_plugin):
    current_dir = pathlib.Path(os.path.abspath(__file__)).parent
    test_input = os.path.join(current_dir.parent, "rds_test_data.json")

    # if test key does not exist in the result, the test will fail.
    # we need to add rds_old_date_threshold to the json file.
    write: bool = False
    test_data = os.path.join(current_dir.parent, "rds_test_data.json")
    with open(test_data, "r") as file:
        data = json.load(file)
        if "rds_old_date_threshold" not in data:
            data["rds_old_date_threshold"] = int(
                (datetime.now() - timedelta(days=10)).timestamp() * 1e9
            )
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
        "StorageType",
    ]
    result = test_input_plugin(test_input, RDSOldSnapshots)

    # check that result has the needed keys
    details = result.details
    for key in needed_keys:
        assert key in details["rds_old_snapshots"][0]
