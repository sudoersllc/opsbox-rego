import datetime
import json
import os
import pathlib


# ruff: noqa: S101
def test_unused_buckets(rego_process):
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

    rego_policy = os.path.join(current_dir, "unused_buckets.rego")
    rego_input = os.path.join(current_dir.parent, "s3_test_data.json")

    needed_keys = ["last_modified", "name", "storage_class"]
    result = rego_process(
        rego_policy, rego_input, "data.aws.cost.unused_buckets", ["unused_buckets"]
    )
    for x in result["unused_buckets"]:
        for key in needed_keys:
            assert key in x, f"Key {key} not found in {x}"
