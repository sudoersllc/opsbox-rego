# test_rds_old_snapshots.py

import os
import pathlib

def test_rds_old_snapshots(rego_process):
    current_dir = pathlib.Path(os.path.abspath(__file__)).parent
    rego_policy = os.path.join(current_dir, "rds_old_snapshots.rego")
    rego_input = os.path.join(current_dir.parent.parent, "rds_test_data.json")

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