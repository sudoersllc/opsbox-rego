import os
import pathlib
from .empty_zones.empty_zones import EmptyZones


# ruff: noqa: S101
def test_empty_zones(test_input_plugin):
    """Test for unused zones"""
    # Load rego policy
    current_dir = pathlib.Path(os.path.abspath(__file__)).parent

    test_data_path = os.path.join(current_dir.parent, "r53_test_data.json")

    needed_keys = ["id", "name", "private_zone", "record_count"]
    result = test_input_plugin(
        test_data_path, EmptyZones
    ).details["empty_hosted_zones"]
    for item in result:
        for key in needed_keys:
            assert key in item, f"Key {key} not found in item {item}"