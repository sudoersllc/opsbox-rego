import os
import pathlib


# ruff: noqa: S101
def test_storage_class_usage(rego_process):
    """Test for storage class usage policy"""
    # Load rego policy
    current_dir = pathlib.Path(os.path.abspath(__file__)).parent

    rego_policy = os.path.join(current_dir, "storage_class_usage.rego")
    rego_input = os.path.join(current_dir.parent.parent, "s3_test_data.json")


    needed_keys = ["percentage_glacier_or_standard_ia","glacier_or_standard_ia_buckets"]
    rego_process(rego_policy, rego_input, "data.aws.cost.storage_class_usage", needed_keys)

