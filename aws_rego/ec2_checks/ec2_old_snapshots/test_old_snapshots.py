import datetime
import json
import os
import pathlib
from .ec2_old_snapshots.ec2_old_snapshots import EC2OLD
# ruff: noqa: S101


def test_idle_instances(test_input_plugin):
    """Test for idle instances rego policy"""
    # Load rego policy
    current_dir = pathlib.Path(os.path.abspath(__file__)).parent

    # if test key does not exist in the result, the test will fail.
    # we need to add ec2_snapshot_old_threshold to the json file.
    write: bool = False
    test_data = os.path.join(current_dir.parent, "ec2_test_data.json")
    with open(test_data, "r") as file:
        data = json.load(file)
        if "ec2_snapshot_old_threshold" not in data:
            data["ec2_snapshot_old_threshold"] = int(
                (datetime.datetime.now() - datetime.timedelta(days=10)).timestamp()
                * 1e9
            )
            write = True

    # overwrite the file
    if write:
        with open(test_data, "w") as file:
            json.dump(data, file, indent=4)

    test_data_path = os.path.join(current_dir.parent, "ec2_test_data.json")

    needed_keys = [
        "progress",
        "region",
        "snapshot_id",
        "start_time",
        "state",
        "tags",
        "volume_id",
    ]
    result = test_input_plugin(test_data_path, EC2OLD)
    result = result.details["ec2_old_snapshots"]

    for x in result:
        for key in needed_keys:
            assert key in x, f"Key {key} not found in {x}"
