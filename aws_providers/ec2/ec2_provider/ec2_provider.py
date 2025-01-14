from pluggy import HookimplMarker
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import boto3
from loguru import logger
import threading
from typing import Annotated
from core.plugins import Result
import json

# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")

def tag_string_to_dict(tag_string):
    """Converts a string of key-value pairs to a dictionary."""
    if isinstance(tag_string, str):
        try:
            # Attempt to parse the string as JSON
            tag_string = json.loads(tag_string)
            return tag_string
        except json.JSONDecodeError:
            # Handle the error or raise an exception
            raise ValueError("Tags provided are not in a valid JSON format.")

def find_aws_credentials() -> tuple[str, str] | None:
    """Find AWS credentials in the default AWS configuration file.
    
    Returns:
        tuple[str, str] | None: A tuple containing the AWS access key and secret access key, or None if not
            found.
    """
    try:
        session = boto3.Session()
        credentials = session.get_credentials()
        credentials = credentials.get_frozen_credentials()
        access_key = credentials.access_key
        secret_key = credentials.secret_key
        logger.debug("Found default AWS credentials.")
        return access_key, secret_key
    except Exception as _:
        logger.debug("Default AWS credentials not found.")
        return None

def find_default_region() -> str | None:
    """Find the default region in the default AWS configuration file.
    
    Returns:
        str | None: The default region, or None if not found.
    """
    try:
        session = boto3.Session()
        region = session.region_name
        logger.debug(f"Found default AWS region: {region}")
        return region
    except Exception as _:
        logger.debug("Default AWS region not found.")
        return None
    
class EC2Provider:

    """Plugin for gathering data related to AWS EC2 instances, volumes, and Elastic IPs.

    Attributes:
        ec2 (boto3.client): The boto3 client for EC2.
        credentials (dict): A dictionary containing AWS access key, secret access key, and region.
    """

    @hookimpl
    def grab_config(self):
        """Return the plugin's configuration."""

        credentials = find_aws_credentials()
        region = find_default_region()
        class EC2Config(BaseModel):
            """Configuration for the AWS EC2 plugin."""

            aws_access_key_id: Annotated[str, Field(..., description="AWS access key ID", required=True, default=credentials[0])]
            aws_secret_access_key: Annotated[str, Field(..., description="AWS secret access key", required=True, default=credentials[1])]
            aws_region: Annotated[str |  None, Field(description="AWS region", required=False,default=region)]
            volume_tags: Annotated[
                str | None, Field(description="Key-value tag pairs for volumes", required=False, default=None)
            ]
            instance_tags: Annotated[
                str | None, Field(description="Key-value tag pairs for instances", required=False, default=None)
            ]
            eip_tags: Annotated[
                str | None, Field(description="Key-value tag pairs for Elastic IPs", required=False, default=None)
            ]

        return EC2Config
                

    @hookimpl
    def activate(self) -> None:
        """Initialize the plugin."""
        logger.trace("Activating EC2 plugin...")

    @hookimpl
    def set_data(self, model: type[BaseModel]) -> None:
        """Set the data for the plugin based on the model."""
        logger.trace("Setting data for EC2 plugin...")
        self.credentials = model.model_dump()

    @hookimpl
    def gather_data(self):
        """
        Gathers data related to AWS EC2 instances, volumes, and Elastic IPs.

        Returns:
            dict: A dictionary containing the gathered data of the format:
                "input": {
                        "volumes": [
                            {
                                "volume_id": "vol-1234567890abcdef0",
                                "state": "available",
                                "size": 8,
                                "create_time": "2021-06-01T00:00:00",
                                "region": "us-west-1"
                            },
                            ...
                        ],
                        "instances": [
                            {
                                "instance_id": "i-1234567890abcdef0",
                                "state": "running",
                                "avg_cpu_utilization": 0.0,
                                "region": "us-west-1"
                            },
                            ...
                        ]
                    }
        """
        logger.info("Gathering data for AWS EC2 instances, volumes, Snapshots, and Elastic IPs...")
        credentials = self.credentials


        if credentials["aws_region"] is None:
            region_client = boto3.client(
                "ec2",
                aws_access_key_id=credentials["aws_access_key_id"],
                aws_secret_access_key=credentials["aws_secret_access_key"],
                region_name="us-west-1",
            )

            regions = [region["RegionName"] for region in region_client.describe_regions()["Regions"]]
            logger.info(f"Regions: {regions}")

        else:
            regions = credentials["aws_region"].split(",")

        all_volumes = []
        all_instances = []
        all_snapshots = []
        all_eips = []
        threads = []

        def process_region(region):
            """Process data for a specific AWS region."""
            logger.debug(f"Gathering data for region {region}...")
            regional_ec2 = boto3.client(
                "ec2",
                aws_access_key_id=credentials["aws_access_key_id"],
                aws_secret_access_key=credentials["aws_secret_access_key"],
                region_name=region,
            )

            # Gather volumes data
            paginator = regional_ec2.get_paginator("describe_volumes")
            # if tags key-value pairs are provided, filter volumes based on tags

            if credentials["volume_tags"]:
                tags = tag_string_to_dict(credentials["volume_tags"])
                volume_filters = [
                    {"Name": "status", "Values": ["available"]},
                ]  # Iterate through the tags dictionary and add them to the filters
                for key, value in tags.items():
                    volume_filters.append({"Name": f"tag:{key}", "Values": [value]})
            else:
                volume_filters = [{"Name": "status", "Values": ["available"]}]

            for page in paginator.paginate(Filters=volume_filters):
                for volume in page["Volumes"]:
                    tags = {tag["Key"]: tag["Value"] for tag in volume.get("Tags", [])}

                    all_volumes.append(
                        {
                            "volume_id": volume["VolumeId"],
                            "state": volume["State"],
                            "size": volume["Size"],
                            "create_time": volume["CreateTime"].isoformat(),
                            "region": region,
                            "tags": tags,
                        }
                    )
            # Gather instances data

            instance_filters = []

            if credentials["instance_tags"]:
                instance_tags = tag_string_to_dict(credentials["instance_tags"])

                for key, value in instance_tags.items():
                    instance_filters.append({"Name": f"tag:{key}", "Values": [value]})

            # Use instance_filters if available
            instances = regional_ec2.describe_instances(Filters=instance_filters) if instance_filters else regional_ec2.describe_instances()

            for reservation in instances["Reservations"]:
                for instance in reservation["Instances"]:
                    instance_id = instance["InstanceId"]
                    state = instance["State"]["Name"]
                    instance_type = instance["InstanceType"]
                    ami_id = instance["ImageId"]
                    tenancy = instance.get("Placement", {}).get("Tenancy", "shared")  # Default to 'shared'
                    virtualization_type = instance.get("VirtualizationType", "hvm")  # Default to 'hvm'
                    ebs_optimized = instance.get("EbsOptimized", False)  # True or False
                    porcessor = instance.get("ProcessorInfo", "Unknown")  # Default to 'Unknown'
                    tags = instance.get("Tags", [])

                    # Describe the AMI to get the operating system
                    ami_response = regional_ec2.describe_images(ImageIds=[ami_id])
                    operating_system = ami_response["Images"][0].get("PlatformDetails", "Unknown") if ami_response["Images"] else "Unknown"

                    # Gather CPU utilization from CloudWatch
                    cloudwatch = boto3.client(
                        "cloudwatch",
                        aws_access_key_id=credentials["aws_access_key_id"],
                        aws_secret_access_key=credentials["aws_secret_access_key"],
                        region_name=region,
                    )

                    end_time = datetime.utcnow()
                    start_time = end_time - timedelta(days=7)

                    response = cloudwatch.get_metric_statistics(
                        Namespace="AWS/EC2",
                        MetricName="CPUUtilization",
                        Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=3600,  # One-hour granularity
                        Statistics=["Average"],
                    )

                    datapoints = response["Datapoints"]
                    avg_cpu_utilization = sum(dp["Average"] for dp in datapoints) / len(datapoints) if datapoints else 0.0

                    tags = {tag["Key"]: tag["Value"] for tag in instance.get("Tags", [])}

                    all_instances.append(
                        {
                            "instance_id": instance_id,
                            "state": state,
                            "avg_cpu_utilization": avg_cpu_utilization,
                            "region": region,
                            "instance_type": instance_type,
                            "operating_system": operating_system,
                            "tenancy": tenancy,
                            "virtualization_type": virtualization_type,
                            "ebs_optimized": ebs_optimized,
                            "processor": porcessor,
                            "tags": tags,
                        }
                    )

            if credentials["eip_tags"]:
                eip_tags = tag_string_to_dict(credentials["eip_tags"])
                eip_filters = []
                for key, value in eip_tags.items():
                    eip_filters.append({"Name": f"tag:{key}", "Values": [value]})

                eips = regional_ec2.describe_addresses(Filters=eip_filters)["Addresses"]
            else:
                eips = regional_ec2.describe_addresses()["Addresses"]

            for eip in eips:
                all_eips.append(
                    {
                        "public_ip": eip["PublicIp"],
                        "association_id": eip.get("AssociationId", ""),
                        "domain": eip["Domain"],
                        "region": region,
                    }
                )
            snapshot_filters = []

            if credentials.get("volume_tags"):  # Assuming you want to filter snapshots by volume tags
                tags = tag_string_to_dict(credentials["volume_tags"])
                for key, value in tags.items():
                    snapshot_filters.append({"Name": f"tag:{key}", "Values": [value]})

            paginator = regional_ec2.get_paginator("describe_snapshots")

            for page in paginator.paginate(OwnerIds=["self"], Filters=snapshot_filters):
                for snapshot in page["Snapshots"]:
                    tags = {tag["Key"]: tag["Value"] for tag in snapshot.get("Tags", [])}

                    all_snapshots.append(
                        {
                            "snapshot_id": snapshot["SnapshotId"],
                            "volume_id": snapshot["VolumeId"],
                            "state": snapshot["State"],
                            "start_time": snapshot["StartTime"].isoformat(),
                            "progress": snapshot.get("Progress", "0%"),
                            "region": region,
                            "tags": tags,
                        }
                    )

        # Create threads for each region to gather data concurrently
        for region in regions:
            thread = threading.Thread(target=process_region, args=(region,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        internal = {
            "aws_ec2": all_volumes,
            "aws_ec2_instances": all_instances,
            "aws_ec2_eips": all_eips,
            "aws_ec2_snapshots": all_snapshots
        }

        # Prepare the data in a format that can be consumed by Rego
        rego_ready_data = {
            "input": {
                "volumes": internal.get("aws_ec2", []),
                "instances": internal.get("aws_ec2_instances", []),
                "eips": internal.get("aws_ec2_eips", []),
                "snapshots": internal.get("aws_ec2_snapshots", [])
            }
        }

        logger.trace(rego_ready_data)

        item = Result(
            relates_to="ec2",
            result_name="ec2_data",
            result_description="Gathered data related to EC2 instances, volumes, and Elastic IPs.",
            formatted="",
            details=rego_ready_data,
        )

        return item
    