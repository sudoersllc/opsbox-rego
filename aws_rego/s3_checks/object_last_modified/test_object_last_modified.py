import datetime
import json
import os
import pathlib


# ruff: noqa: S101
def test_object_last_modified(rego_process):
    """Test for object last modified policy"""
    # Load rego policy
    current_dir = pathlib.Path(os.path.abspath(__file__)).parent

    rego_policy = os.path.join(current_dir, "object_last_modified.rego")
    rego_input = os.path.join(current_dir.parent.parent, "s3_test_data.json")

    # if test key does not exist in the result, the test will fail.
    # we need to add s3_last_modified_date_threshold to the json file.
    write: bool = False
    test_data = os.path.join(current_dir.parent.parent, "s3_test_data.json")
    with open(test_data, "r") as file:
        data = json.load(file)
        if "s3_last_modified_date_threshold" not in data:
            data["s3_last_modified_date_threshold"] = int(
                (datetime.datetime.now() - datetime.timedelta(days=10)).timestamp()
            )
            write = True

    # overwrite the file
    if write:
        with open(test_data, "w") as file:
            json.dump(data, file, indent=4)

    needed_keys = [
        "percentage_standard_and_old",
        "standard_and_old_objects",
        "total_objects",
    ]
    rego_process(
        rego_policy, rego_input, "data.aws.cost.object_last_modified", needed_keys
    )
