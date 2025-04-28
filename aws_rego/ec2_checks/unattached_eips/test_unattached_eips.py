import os
import pathlib
from .unattached_eips.unattached_eips import UnattachedEips


def test_unattached_eips(test_input_plugin):
    """Test for idle instances rego policy"""
    # Load rego policy
    current_dir = pathlib.Path(os.path.abspath(__file__)).parent

    test_data_path = os.path.join(current_dir.parent, "ec2_test_data.json")
    needed_keys = ["association_id", "domain", "public_ip", "region"]
    result = test_input_plugin(test_data_path, UnattachedEips)
    result = result.details

    for x in result:
        for key in needed_keys:
            assert key in x, f"Key {key} not found in {x}"