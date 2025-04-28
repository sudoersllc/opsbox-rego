import os
import pathlib
from .stray_ebs.stray_ebs import StrayEbs


def test_idle_instances(test_input_plugin):
    """Test for idle instances rego policy"""
    # Load rego policy
    current_dir = pathlib.Path(os.path.abspath(__file__)).parent

    test_data_path = os.path.join(current_dir.parent, "ec2_test_data.json")
    needed_keys = ["create_time", "region", "size", "state", "tags"]
    result = test_input_plugin(test_data_path, StrayEbs)

    result = result.details
    for x in result:
        info = x[next(iter(x))]
        for key in needed_keys:
            assert key in info, f"Key {key} not found in {info}"
