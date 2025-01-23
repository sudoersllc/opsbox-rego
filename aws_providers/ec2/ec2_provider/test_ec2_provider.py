from moto import mock_aws
from .ec2_provider.ec2_provider import EC2Provider
from pydantic import BaseModel
import boto3
from datetime import datetime

# ruff: noqa: S101
@mock_aws
def test_gather_data(json_output=False):
    """Test of the EC2 provider gather_data method.

    Args:
        json_output (bool, optional): If True, the test will output the JSON result to a file. Defaults to False.
            File will be saved to ./ec2_test_data.json.
    """
    provider = EC2Provider()

    class MockModel(BaseModel):
        aws_access_key_id: str = "test_access_key"
        aws_secret_access_key: str = "test_secret_key"
        aws_region: str = "us-west-1"
        volume_tags: str = None
        instance_tags: str = None
        eip_tags: str = None

    model = MockModel()
    provider.set_data(model)

    # Create mock EC2 resources
    ec2 = boto3.client("ec2", region_name="us-west-1")
    ec2_resource = boto3.resource("ec2", region_name="us-west-1")

    # Register a mock AMI
    ami_response = ec2.register_image(
        Name="TestAMI",
        Description="A mock AMI for testing",
        Architecture="x86_64",
        RootDeviceName="/dev/sda1",
        VirtualizationType="hvm",
        BlockDeviceMappings=[
            {
                "DeviceName": "/dev/sda1",
                "Ebs": {
                    "VolumeSize": 8,
                },
            },
        ],
    )
    ami_id = ami_response["ImageId"]

    # Run an instance and capture its ID
    instances = ec2_resource.create_instances(
        ImageId=ami_id,
        MinCount=1,
        MaxCount=1
    )
    instance_id = instances[0].id

    # Create a volume and capture its ID
    volume = ec2_resource.create_volume(Size=8, AvailabilityZone="us-west-1a")
    volume_id = volume.id

    # Allocate an Elastic IP
    eip_response = ec2.allocate_address(Domain="vpc")
    allocation_id = eip_response.get("AllocationId")

    # Ensure AllocationId is present
    assert allocation_id is not None, "AllocationId is missing from EIP response"

    # Create a snapshot
    snapshot = ec2_resource.create_snapshot(VolumeId=volume_id, Description="Test snapshot")
    snapshot_id = snapshot.id

    # Create mock CloudWatch metrics
    cloudwatch = boto3.client("cloudwatch", region_name="us-west-1")
    cloudwatch.put_metric_data(
        Namespace="AWS/EC2",
        MetricData=[
            {
                "MetricName": "CPUUtilization",
                "Dimensions": [{"Name": "InstanceId", "Value": instance_id}],
                "Timestamp": datetime.utcnow(),
                "Value": 10.0,
                "Unit": "Percent",
            },
        ],
    )

    # Gather data using your provider
    result = provider.gather_data()
    assert result is not None

    if json_output:
        import json

        with open("ec2_test_data.json", "w") as f:
            json.dump(result.model_dump()["details"]["input"], f, indent=4)

    assert "input" in result.details
    assert "volumes" in result.details["input"]
    assert "instances" in result.details["input"]
    assert "eips" in result.details["input"]

    # Validate that the data matches what we created
    volumes = result.details["input"]["volumes"]
    instances = result.details["input"]["instances"]
    eips = result.details["input"]["eips"]
    snapshots = result.details["input"]["snapshots"]

    # Assert volumes
    assert len(volumes) == 1
    assert volumes[0]["volume_id"] == volume_id
    assert volumes[0]["state"] == "available"
    assert volumes[0]["size"] == 8
    assert volumes[0]["region"] == "us-west-1"

    # Assert instances
    assert len(instances) == 1
    assert instances[0]["instance_id"] == instance_id
    assert instances[0]["state"] == "running"
    assert instances[0]["region"] == "us-west-1"

    # Assert EIPs
    assert len(eips) == 1
    assert eips[0]["region"] == "us-west-1"

    # Assert snapshots
    assert len(snapshots) != 0
    snapshot_ids = [snap["snapshot_id"] for snap in snapshots]
    volume_ids = [snap["volume_id"] for snap in snapshots]
    assert snapshot_id in snapshot_ids
    assert volume_id in volume_ids