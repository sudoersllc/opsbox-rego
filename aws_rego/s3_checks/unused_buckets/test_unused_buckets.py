import datetime
import json
import os
import pathlib
from .unused_buckets.unused_buckets import UnusedBuckets


# ruff: noqa: S101
def test_unused_buckets(test_input_plugin):
    """Test for unused buckets policy"""
    # Load rego policy
    current_dir = pathlib.Path(os.path.abspath(__file__)).parent

    # if test key does not exist in the result, the test will fail.
    # we need to add s3_unused_bucket_date_threshold to the json file.
    write: bool = False
    test_data = os.path.join(current_dir.parent, "s3_test_data.json")
    with open(test_data, "r") as file:
        data = json.load(file)
        if "s3_unused_bucket_date_threshold" not in data:
            data["s3_unused_bucket_date_threshold"] = int(
                (datetime.datetime.now() - datetime.timedelta(days=10)).timestamp()
            )
            write = True

    # overwrite the file
    if write:
        with open(test_data, "w") as file:
            json.dump(data, file, indent=4)

    test_data_path = os.path.join(current_dir.parent, "s3_test_data.json")

    needed_keys = ["last_modified", "name", "storage_class"]
    result = test_input_plugin(test_data_path, UnusedBuckets).details
    for x in result:
        for key in needed_keys:
            assert key in x, f"Key {key} not found in {x}"
