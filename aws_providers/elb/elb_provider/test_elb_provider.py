from moto import mock_aws
import boto3
from .elb_provider.elb_provider import elbProvider
from opsbox import Result
from pydantic import BaseModel
from loguru import logger


# ruff: noqa: S101
@mock_aws
def test_elb_provider_gather_data(json_output=False):
    """Test of the ELB provider gather_data method.

    Args:
        json_output (bool, optional): If True, the test will output the JSON result to a file. Defaults to False.
            File will be saved to ./elb_test_data.json.
    """

    # Mock AWS credentials (moto uses dummy credentials)
    aws_access_key_id = "fake_access_key"
    aws_secret_access_key = "fake_secret_key"  # noqa: S105
    aws_region = "us-east-1"

    # Create mock VPC and Subnet
    ec2_client = boto3.client("ec2", region_name=aws_region)
    vpc_response = ec2_client.create_vpc(CidrBlock="10.0.0.0/16")
    vpc_id = vpc_response["Vpc"]["VpcId"]

    subnet_response = ec2_client.create_subnet(
        VpcId=vpc_id, CidrBlock="10.0.1.0/24", AvailabilityZone=aws_region + "a"
    )
    subnet_id = subnet_response["Subnet"]["SubnetId"]

    # Create mock Classic Load Balancer
    elb_client = boto3.client("elb", region_name=aws_region)
    elb_client.create_load_balancer(
        LoadBalancerName="test-classic-lb",
        Listeners=[
            {
                "Protocol": "HTTP",
                "LoadBalancerPort": 80,
                "InstancePort": 80,
            },
        ],
        AvailabilityZones=[aws_region + "a"],
    )

    # Create mock Application Load Balancer
    elbv2_client = boto3.client("elbv2", region_name=aws_region)
    alb_response = elbv2_client.create_load_balancer(
        Name="test-alb",
        Subnets=[subnet_id],
        Scheme="internet-facing",
        Type="application",
        IpAddressType="ipv4",
    )
    alb_arn = alb_response["LoadBalancers"][0]["LoadBalancerArn"]

    # Create target group and register targets
    tg_response = elbv2_client.create_target_group(
        Name="test-target-group",
        Protocol="HTTP",
        Port=80,
        VpcId=vpc_id,
        TargetType="instance",
    )
    target_group_arn = tg_response["TargetGroups"][0]["TargetGroupArn"]

    elbv2_client.register_targets(
        TargetGroupArn=target_group_arn,
        Targets=[{"Id": "i-1234567890abcdef0"}],
    )

    # Create listener for the ALB
    elbv2_client.create_listener(
        LoadBalancerArn=alb_arn,
        Protocol="HTTP",
        Port=80,
        DefaultActions=[{"Type": "forward", "TargetGroupArn": target_group_arn}],
    )

    # Instantiate the provider and set credentials
    provider = elbProvider()

    class MockCredentials(BaseModel):
        aws_access_key_id: str
        aws_secret_access_key: str
        aws_region: str

    credentials = MockCredentials(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_region=aws_region,
    )

    provider.set_data(credentials)

    # Capture logging output (optional)
    logger.remove()
    logger.add(lambda msg: None)  # Disable logging for test clarity

    # Invoke gather_data method
    result = provider.gather_data()

    if json_output:
        import json

        with open("elb_test_data.json", "w") as f:
            json.dump(result.model_dump()["details"]["input"], f, indent=4)

    # Assertions
    assert isinstance(result, Result)
    assert result.relates_to == "elb"
    assert result.result_name == "elb_info"
    assert "elbs" in result.details["input"]
    elbs = result.details["input"]["elbs"]
    assert len(elbs) == 2  # We created 2 load balancers

    # Verify Classic Load Balancer data
    classic_lb = next((elb for elb in elbs if elb["Type"] == "Classic"), None)
    assert classic_lb is not None
    assert classic_lb["Name"] == "test-classic-lb"

    # Verify Application Load Balancer data
    alb = next((elb for elb in elbs if elb["Type"] == "application"), None)
    assert alb is not None
    assert alb["Name"] == "test-alb"
