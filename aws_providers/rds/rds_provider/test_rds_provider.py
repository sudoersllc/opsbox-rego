from moto import mock_aws
import boto3
import sys
import os

# Add the root directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))
from rds_provider import RDSProvider
from core.plugins import Result
from pydantic import BaseModel
from loguru import logger

# ruff: noqa: S101
@mock_aws
def test_rds_provider_gather_data(json_output=False):
    """Test of the RDS provider gather_data method.
    
    Args:
        json_output (bool, optional): If True, the test will output the JSON result to a file. Defaults to False.
            File will be saved to tests/data/rds_test_data.json.
    """
    
    # Mock AWS credentials (moto uses dummy credentials)
    aws_access_key_id = "fake_access_key"
    aws_secret_access_key = "fake_secret_key"  # noqa: S105
    aws_region = "us-west-1"

    # Create mock RDS client
    rds_client = boto3.client("rds", region_name=aws_region)

    # Create mock RDS instance
    rds_client.create_db_instance(
        DBInstanceIdentifier="test-instance",
        AllocatedStorage=20,
        DBInstanceClass="db.t2.micro",
        Engine="mysql",
        MasterUsername="admin",
        MasterUserPassword="password",
        AvailabilityZone=aws_region + "a",
    )

    # Create mock RDS snapshot
    rds_client.create_db_snapshot(
        DBSnapshotIdentifier="test-snapshot",
        DBInstanceIdentifier="test-instance",
    )

    # Instantiate provider and set credentials
    provider = RDSProvider()

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

        with open("tests\data\\rds_test_data.json", "w") as f:
            json.dump(result.model_dump()["details"]["input"], f, indent=4)

    # Assertions
    assert isinstance(result, Result)
    assert result.relates_to == "rds"
    assert result.result_name == "rds_instances"
    details = result.details["input"]
    assert "rds_instances" in details
    assert "rds_snapshots" in details

    # Verify RDS instances data
    instances = details["rds_instances"]
    assert len(instances) == 1
    instance = instances[0]
    assert instance["InstanceIdentifier"] == "test-instance"
    assert instance["InstanceType"] == "db.t2.micro"
    assert instance["Engine"] == "mysql"
    assert instance["AllocatedStorage"] == 20
    # Metrics may not be available in moto's mock, so check for default values
    assert "CPUUtilization" in instance
    assert "Connections" in instance
    assert "StorageUtilization" in instance

    # Verify RDS snapshots data
    snapshots = details["rds_snapshots"]
    assert len(snapshots) == 1
    snapshot_list = snapshots[0]
    assert len(snapshot_list) == 1
    snapshot = snapshot_list[0]
    assert snapshot["SnapshotIdentifier"] == "test-snapshot"
    assert snapshot["InstanceIdentifier"] == "test-instance"
