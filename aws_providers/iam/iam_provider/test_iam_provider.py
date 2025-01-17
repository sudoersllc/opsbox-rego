from moto import mock_aws
import boto3
import json
from .iam_provider.iam_provider import IAMProvider
from core.plugins import Result
from pydantic import BaseModel


# ruff: noqa: S101
@mock_aws
def test_iam_provider_gather_data(json_output=False):
    """Test of the IAM provider gather_data method.

    Args:
        json_output (bool, optional): If True, the test will output the JSON result to a file. Defaults to False.
            File will be saved to ./iam_test_data.json.
    """
    # Mock AWS credentials (moto uses dummy credentials)
    aws_access_key_id = "fake_access_key"
    aws_secret_access_key = "fake_secret_key"  # noqa: S105
    aws_region = "us-west-1"

    # Create mock IAM client
    iam_client = boto3.client("iam", region_name=aws_region)

    # Create mock user
    iam_client.create_user(UserName="test-user")

    # Create mock role
    iam_client.create_role(RoleName="test-role", AssumeRolePolicyDocument="{}")

    # Create valid policy document
    policy_document = {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Action": "*", "Resource": "*"}]}

    # Create mock policy
    iam_client.create_policy(PolicyName="test-policy", PolicyDocument=json.dumps(policy_document))

    # Generate credential report
    iam_client.generate_credential_report()

    # Instantiate provider and set credentials
    provider = IAMProvider()

    class MockCredentials(BaseModel):
        aws_access_key_id: str
        aws_secret_access_key: str
        aws_region: str | None

    credentials = MockCredentials(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_region=aws_region,
    )

    provider.set_data(credentials)

    # Invoke gather_data method
    result = provider.gather_data()

    if json_output:
        with open("iam_test_data.json", "w") as f:
            json.dump(result.model_dump()["details"]["input"], f, indent=4)

    # Assertions
    assert isinstance(result, Result)
    assert result.relates_to == "aws_data"
    assert result.result_name == "aws_iam_data"
    details = result.details["input"]
    assert "iam_users" in details
    assert "iam_roles" in details
    assert "iam_policies" in details
    assert "credential_report" in details

    # Verify IAM users data
    iam_users = details["iam_users"]
    assert len(iam_users) == 1
    assert iam_users[0]["user_name"] == "test-user"

    # Verify IAM roles data
    iam_roles = details["iam_roles"]
    assert len(iam_roles) == 1
    assert iam_roles[0]["role_name"] == "test-role"

    # Verify IAM policies data
    iam_policies = details["iam_policies"]
    assert len(iam_policies) == 1
    assert iam_policies[0]["policy_name"] == "test-policy"

    # Verify credential report data
    credential_report = details["credential_report"]
    users_in_report = [entry["user"] for entry in credential_report]
    assert "test-user" in users_in_report
