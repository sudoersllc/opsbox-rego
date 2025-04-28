import json
import os
import pathlib
from .unused_policies.unused_policies import UnusedIAMPolicies


def test_unused_policies(test_input_plugin):
    """Test for unused policies"""
    current_dir = pathlib.Path(os.path.abspath(__file__)).parent
    rego_input = os.path.join(current_dir.parent, "iam_test_data.json")

    needed_keys = [
        "Arn",
        "AttachmentCount",
        "CreateDate",
        "DefaultVersionId",
        "Description",
        "IsAttachable",
        "Path",
        "PolicyId",
        "PolicyName",
        "UpdateDate",
        "attached_to"
    ]

    result = test_input_plugin(rego_input, UnusedIAMPolicies)
    # check that result has the needed keys
    details = result.details
    for policy in details:
        for key in needed_keys:
            assert key in policy
