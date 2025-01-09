import os
import pathlib


# ruff: noqa: S101
def test_overdue_api_keys(rego_process):
    """Test for overdue api keys policy"""
    # Load rego policy
    current_dir = pathlib.Path(os.path.abspath(__file__)).parent

    rego_policy = os.path.join(current_dir, "overdue_api_keys.rego")
    rego_input = os.path.join(current_dir.parent.parent, "iam_test_data.json")

    result = rego_process(rego_policy, rego_input, "data.aws.cost.overdue_api_keys", ["overdue_api_keys"])
    needed_keys = [
        "access_key_1_active",
        "access_key_1_last_rotated",
        "access_key_1_last_used_date",
        "access_key_1_last_used_region",
        "access_key_1_last_used_service",
        "access_key_2_active",
        "access_key_2_last_rotated",
        "access_key_2_last_used_date",
        "access_key_2_last_used_region",
        "access_key_2_last_used_service",
        "arn",
        "cert_1_active",
        "cert_1_last_rotated",
        "cert_2_active",
        "cert_2_last_rotated",
        "mfa_active",
        "password_enabled",
        "password_last_changed",
        "password_last_used",
        "password_next_rotation",
        "user",
        "user_creation_time"
    ]
    for x in result["overdue_api_keys"]:
        for key in needed_keys:
            assert key in x, f"Key {key} not found in {x}"
