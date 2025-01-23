from moto import mock_aws
import boto3
import sys
import os

# Add the root directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))
from s3_provider import S3Provider
from core.plugins import Result
from pydantic import BaseModel
from loguru import logger


# ruff: noqa: S101
@mock_aws
def test_s3_provider_gather_data(json_output=False):
    """Test of the S3 provider gather_data method.
    
    Args:
        json_output (bool, optional): If True, the test will output the JSON result to a file. Defaults to False.
            File will be saved to tests/data/s3_test_data.json.
    """
    # Mock AWS credentials (moto uses dummy credentials)
    aws_access_key_id = "fake_access_key"
    aws_secret_access_key = "fake_secret_key"  # noqa: S105
    aws_region = "us-west-1"

    # Create mock S3 client
    s3_client = boto3.client("s3", region_name=aws_region)

    # Create mock S3 buckets with LocationConstraint
    s3_client.create_bucket(Bucket="test-bucket-1", CreateBucketConfiguration={"LocationConstraint": aws_region})
    s3_client.create_bucket(Bucket="test-bucket-2", CreateBucketConfiguration={"LocationConstraint": aws_region})

    # Add mock objects to bucket 1
    s3_client.put_object(Bucket="test-bucket-1", Key="test-object-1", Body="content1")
    s3_client.put_object(Bucket="test-bucket-1", Key="test-object-2", Body="content2")

    # Add mock objects to bucket 2
    s3_client.put_object(Bucket="test-bucket-2", Key="test-object-3", Body="content3", StorageClass="GLACIER")

    # Instantiate provider and set credentials
    provider = S3Provider()

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

        with open("tests/data/s3_test_data.json", "w") as f:
            json.dump(result.model_dump()["details"]["input"], f, indent=4)

    # Assertions
    assert isinstance(result, Result)
    assert result.relates_to == "s3"
    assert result.result_name == "s3_info"
    details = result.details["input"]
    assert "buckets" in details
    assert "objects" in details
    assert "current_time" in details

    # Verify bucket data
    buckets = details["buckets"]
    assert len(buckets) == 2
    bucket_names = [bucket["name"] for bucket in buckets]
    assert "test-bucket-1" in bucket_names
    assert "test-bucket-2" in bucket_names

    # Verify object data
    objects = details["objects"]
    assert len(objects) == 3
    object_keys = [obj["Key"] for obj in objects]
    assert "test-object-1" in object_keys
    assert "test-object-2" in object_keys
    assert "test-object-3" in object_keys

    # Verify storage classes
    for obj in objects:
        if obj["Key"] == "test-object-3":
            assert obj["StorageClass"] == "GLACIER"
        else:
            assert obj["StorageClass"] == "STANDARD"
