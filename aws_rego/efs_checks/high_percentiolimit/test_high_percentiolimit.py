import os
import json
import pathlib


def test_high_percent_io_limit(rego_process):
    current_dir = pathlib.Path(os.path.abspath(__file__)).parent

    # if test key does not exist in the result, the test will fail.
    # we need to add efs_percent_io_limit_threshold to the json file.
    write: bool = False
    test_data = os.path.join(current_dir.parent, "efs_test_data.json")
    with open(test_data, "r") as file:
        data = json.load(file)
        if "efs_percent_io_limit_threshold" not in data:
            data["efs_percent_io_limit_threshold"] = 1
            write = True

    # overwrite the file
    if write:
        with open(test_data, "w") as file:
            json.dump(data, file, indent=4)

    # Load rego policy
    rego_policy = os.path.join(current_dir, "high_percentiolimit.rego")
    rego_input = os.path.join(current_dir.parent, "efs_test_data.json")
    needed_keys = ["Id", "Name", "PercentIOLimit"]

    result = rego_process(
        rego_policy,
        rego_input,
        "data.aws_rego.efs_checks.high_percentiolimit.high_percentiolimit.details",
    )
    # check that result has the needed keys
    for key in needed_keys:
        assert key in result[0]
