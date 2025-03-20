import json

import boto3
from moto import mock_aws
from pydantic import BaseModel

# Adjust these imports as needed.
from .efs_provider.efs_provider import efsProvider   # type: ignore
from opsbox import Result

@mock_aws
def test_efs_provider_gather_data(monkeypatch, json_output=True):
    """
    Test the efsProvider.gather_data method.
    
    This test uses @mock_aws to intercept all AWS service calls. It creates a fake
    EFS file system and patches the boto3 client for EFS and CloudWatch to inject
    a file system name and a dummy metric value.
    
    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest monkeypatch fixture.
        json_output (bool, optional): If True, writes JSON output to a file.
    """
    aws_region = "us-east-1"

    # Create a fake EFS file system. The mock_aws decorator will intercept this call.
    efs_client = boto3.client("efs", region_name=aws_region)
    fs_response = efs_client.create_file_system(CreationToken="test-token")
    fs_id = fs_response["FileSystemId"]

    # Monkey-patch boto3.client to adjust responses for "efs" and "cloudwatch".
    original_boto3_client = boto3.client

    def fake_boto3_client(service_name, *args, **kwargs):
        client = original_boto3_client(service_name, *args, **kwargs)
        if service_name == "efs":
            orig_describe = client.describe_file_systems

            def new_describe_file_systems(*args, **kwargs):
                result = orig_describe(*args, **kwargs)
                # Inject a 'Name' field for each file system.
                for fs in result.get("FileSystems", []):
                    fs["Name"] = "TestEFS"
                return result

            client.describe_file_systems = new_describe_file_systems
        elif service_name == "cloudwatch":
            # Override get_metric_statistics to return a dummy datapoint.
            def new_get_metric_statistics(*args, **kwargs):
                return {"Datapoints": [{"Average": 10}]}
            client.get_metric_statistics = new_get_metric_statistics
        return client

    monkeypatch.setattr(boto3, "client", fake_boto3_client)

    # Setup provider credentials using a simple Pydantic model.
    class MockCredentials(BaseModel):
        aws_access_key_id: str
        aws_secret_access_key: str
        aws_region: str

    credentials = MockCredentials(
        aws_access_key_id="fake_access_key",
        aws_secret_access_key="fake_secret_key",
        aws_region=aws_region,
    )

    # Instantiate the provider and set credentials.
    provider = efsProvider()
    provider.set_data(credentials)

    # Call gather_data (this method uses threads internally).
    result = provider.gather_data()

    if json_output:
        with open("efs_test_data.json", "w") as f:
            json.dump(result.model_dump()["details"]["input"], f, indent=4)

    # Begin assertions.
    assert isinstance(result, Result)
    assert result.relates_to == "efs"
    assert result.result_name == "efs_info"
    assert "efss" in result.details["input"]

    efss = result.details["input"]["efss"]
    # Expect one EFS entry (the one we created).
    assert len(efss) == 1

    efs_entry = efss[0]
    # Verify that the file system entry has the injected name, correct ID, and dummy metric.
    assert efs_entry["Name"] == "TestEFS"
    assert efs_entry["Id"] == fs_id
    assert efs_entry["PercentIOLimit"] == 10
