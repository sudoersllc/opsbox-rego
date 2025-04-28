import json
import os
import pathlib
from .object_last_modified.object_last_modified import ObjectLastModified


def test_object_last_modified(test_input_plugin):
    """Test for object last modified check"""
    current_dir = pathlib.Path(os.path.abspath(__file__)).parent

    # if test key does not exist in the result, the test will fail.
    # we need to add s3_object_age_threshold to the json file.
    write: bool = False
    test_data = os.path.join(current_dir.parent, "s3_test_data.json")
    with open(test_data, "r") as file:
        data = json.load(file)
        if "s3_object_age_threshold" not in data:
            data["s3_object_age_threshold"] = 180
            write = True

    # overwrite the file
    if write:
        with open(test_data, "w") as file:
            json.dump(data, file, indent=4)

    test_data_path = os.path.join(current_dir.parent, "s3_test_data.json")

    needed_keys = [
        "percentage_standard_and_old",
        "standard_and_old_objects",
        "total_objects",
    ]

    result = test_input_plugin(test_data_path, ObjectLastModified)
    # check that result has the needed keys
    details = result.details
    for key in needed_keys:
        assert key in details
