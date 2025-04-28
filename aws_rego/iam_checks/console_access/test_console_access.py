import os
import pathlib
from .console_access.console_access import ConsoleAccessIAM


# ruff: noqa: S101
def test_console_access(test_input_plugin):
    """Test for console access policy"""
    # Load rego policy
    current_dir = pathlib.Path(os.path.abspath(__file__)).parent

    rego_policy = os.path.join(current_dir, "console_access.rego")
    rego_input = os.path.join(current_dir.parent, "iam_test_data.json")

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
        "user_creation_time",
    ]


    result = test_input_plugin(rego_input, ConsoleAccessIAM)
    # check that result has the needed keys
    details = result.details["users_with_console_access"]
    for user in details:
        for key in needed_keys:
            assert key in user