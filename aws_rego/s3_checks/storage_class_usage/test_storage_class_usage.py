import datetime
import json
import os
import pathlib
from .storage_class_usage.storage_class_usage import StorageClassUsage

# ruff: noqa: S101
def test_storage_class_usage(test_input_plugin):
    """Test for storage class usage policy"""
    # Load rego policy
    current_dir = pathlib.Path(os.path.abspath(__file__)).parent

    # if test key does not exist in the result, the test will fail.
    # we need to add s3_stale_bucket_date_threshold to the json file.
    write: bool = False
    test_data = os.path.join(current_dir.parent, "s3_test_data.json")
    with open(test_data, "r") as file:
        data = json.load(file)
        if "s3_stale_bucket_date_threshold" not in data:
            data["s3_stale_bucket_date_threshold"] = int(
                (datetime.datetime.now() - datetime.timedelta(days=10)).timestamp()
            )
            write = True

    # overwrite the file
    if write:
        with open(test_data, "w") as file:
            json.dump(data, file, indent=4)
    test_data_path = os.path.join(current_dir.parent, "s3_test_data.json")

    needed_keys = [
        "percentage_glacier_or_standard_ia",
        "glacier_or_standard_ia_buckets",
        "count_glacier_or_standard_ia",
        "count_stale",
        "count_mixed",
        "percentage_stale",
        "percentage_mixed",
        "stale_buckets",
        "mixed_storage_buckets",
    ]
    
    result = test_input_plugin(test_data_path, StorageClassUsage).details

    for key in needed_keys:
        assert key in result
