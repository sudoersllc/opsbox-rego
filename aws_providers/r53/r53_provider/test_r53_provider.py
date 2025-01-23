from moto import mock_aws
import boto3
import sys
import os

# Add the root directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))
from r53_provider import Route53Provider
from core.plugins import Result
from pydantic import BaseModel
from loguru import logger


# ruff: noqa: S101
@mock_aws
def test_route53_provider_gather_data(json_output=False):
    """Test of the Route53 provider gather_data method.

    Args:
        json_output (bool, optional): If True, the test will output the JSON result to a file. Defaults to False.
            File will be saved to tests/data/r53_test_data.json.
    """
    # Mock AWS credentials (moto uses dummy credentials)
    aws_access_key_id = "fake_access_key"
    aws_secret_access_key = "fake_secret_key" # noqa: S105
    aws_region = "us-west-1"

    # Create mock EC2 client for region discovery
    ec2_client = boto3.client("ec2", region_name=aws_region)
    ec2_client.describe_regions()

    # Create mock Route53 client
    route53_client = boto3.client("route53")

    # Create mock hosted zone
    zone_response = route53_client.create_hosted_zone(
        Name="example.com.",
        CallerReference="test123",
    )
    zone_id = zone_response["HostedZone"]["Id"]

    # Add resource records
    route53_client.change_resource_record_sets(
        HostedZoneId=zone_id,
        ChangeBatch={
            "Changes": [
                {"Action": "CREATE", "ResourceRecordSet": {"Name": "www.example.com.", "Type": "A", "TTL": 300, "ResourceRecords": [{"Value": "192.0.2.1"}]}},
                {"Action": "CREATE", "ResourceRecordSet": {"Name": "api.example.com.", "Type": "CNAME", "TTL": 300, "ResourceRecords": [{"Value": "www.example.com."}]}},
            ]
        },
    )

    # Create mock health check
    _ = route53_client.create_health_check(
        CallerReference="healthcheck123",
        HealthCheckConfig={
            "IPAddress": "192.0.2.1",
            "Port": 80,
            "Type": "HTTP",
            "ResourcePath": "/",
            "FailureThreshold": 3,
        },
    )

    # Instantiate provider and set credentials
    provider = Route53Provider()

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

    # Disable logging for test clarity
    logger.remove()
    logger.add(lambda msg: None)

    # Invoke gather_data method
    result = provider.gather_data()

    if json_output:
        import json

        with open("tests\data\\r53_test_data.json", "w") as f:
            json.dump(result.model_dump()["details"]["input"], f, indent=4)

    # Assertions
    assert isinstance(result, Result)
    assert result.relates_to == "aws_data"
    assert result.result_name == "aws_data"
    details = result.details["input"]
    assert "hosted_zones" in details
    assert "records" in details
    assert "health_checks" in details

    # Verify hosted zones data
    hosted_zones = details["hosted_zones"]
    assert len(hosted_zones) == 1
    assert hosted_zones[0]["name"] == "example.com."

    # Verify records data
    records = details["records"]
    assert len(records) == 2
    record_names = [record["name"] for record in records]
    assert "www.example.com." in record_names
    assert "api.example.com." in record_names

    # Verify health checks data
    health_checks = details["health_checks"]
    assert len(health_checks) == 1
    assert health_checks[0]["type"] == "HTTP"
    assert health_checks[0]["ip_address"] == "192.0.2.1"
