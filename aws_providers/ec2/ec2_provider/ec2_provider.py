from pluggy import HookimplMarker
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import boto3
from loguru import logger
import threading
from typing import Annotated
from core.plugins import Result
import json

# Define a hook implementation marker for the "opsbox" plugin system
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
        """Define and return the configuration model for the EC2 provider.

        This includes AWS credentials and optional tags for filtering EC2 resources.

        Returns:
            EC2Config: The configuration model for the EC2 provider.
        """

        credentials = find_aws_credentials()
        region = find_default_region()

        class EC2Config(BaseModel):
            """Configuration schema for the EC2 provider.

            Attributes:
                aws_access_key_id (str): AWS access key ID.
                aws_secret_access_key (str): AWS secret access key.
                aws_region (str, optional): AWS region. Defaults to None.
                volume_tags (str, optional): Key-value tag pairs for volumes. Defaults to None.
                instance_tags (str, optional): Key-value tag pairs for instances. Defaults to None.
                eip_tags (str, optional): Key-value tag pairs for Elastic IPs. Defaults to None.
            """

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
        """Log a trace message indicating the provider is being activated."""
        logger.trace("Activating EC2 provider...")

    @hookimpl
    def set_data(self, model: type[BaseModel]) -> None:
        """Store the credentials from the model.

        Args:
            model (BaseModel): The configuration model for the EC2 provider.
        """
        logger.trace("Setting data for EC2 provider...")
        self.credentials = model.model_dump()

    @hookimpl
    def gather_data(self):
        """Gather AWS EC2 data including instances, volumes, snapshots, and Elastic IPs.

        Returns:
            Result: A formatted result containing the gathered data.
        """
        logger.info("Gathering data for AWS EC2 instances, volumes, snapshots, and Elastic IPs...")
        credentials = self.credentials

        
        if credentials["aws_region"] is None:
            logger.info("Gathering data for IAM...")
            credentials = self.credentials

            # Use the specified region or default to "us-west-1"
            region = credentials["aws_region"] or "us-west-1"
            
            if credentials["aws_access_key_id"] is None:
                # Use the instance profile credentials
                region_client = boto3.client("ec2", region_name=region)
            else:
                try:
                    region_client = boto3.client(
                        "ec2",
                        aws_access_key_id=credentials["aws_access_key_id"],
                        aws_secret_access_key=credentials["aws_secret_access_key"],
                        region_name=region,
                    )
                    regions = [region["RegionName"] for region in region_client.describe_regions()["Regions"]]

                except Exception as e:
                    logger.error(f"Error creating IAM client: {e}")
                    return Result(
                        relates_to="aws_data",
                        result_name="aws_iam_data",
                        result_description="Structured IAM data using.",
                        formatted="Error creating IAM client.",
                        details={},
                    )

        else:
            regions = credentials["aws_region"].split(",")

        # Containers to store gathered data
        all_volumes = []
        all_instances = []
        all_snapshots = []
        all_eips = []
        threads = []

        # Helper function for multi-thread data gathering
        def process_region(region):
            """Thread-safe function to gather data for a specific AWS region.

            Args:
                region (str): The AWS region to gather data from.
            """
            logger.debug(f"Gathering data for region {region}...")
            regional_ec2 = boto3.client(
                "ec2",
                aws_access_key_id=credentials["aws_access_key_id"],
                aws_secret_access_key=credentials["aws_secret_access_key"],
                region_name=region,
            )

            # Gather volumes
            paginator = regional_ec2.get_paginator("describe_volumes")
            volume_filters = [{"Name": "status", "Values": ["available"]}]
            if credentials["volume_tags"]:
                tags = tag_string_to_dict(credentials["volume_tags"])
                for key, value in tags.items():
                    volume_filters.append({"Name": f"tag:{key}", "Values": [value]})
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

            # Create instance filters if tags are provided
            instance_filters = []
            if credentials["instance_tags"]:
                instance_tags = tag_string_to_dict(credentials["instance_tags"])
                for key, value in instance_tags.items():
                    instance_filters.append({"Name": f"tag:{key}", "Values": [value]})

            # Gather instances
            instances = regional_ec2.describe_instances(Filters=instance_filters) if instance_filters else regional_ec2.describe_instances()

            # Format and gather cpu utilization data
            for reservation in instances["Reservations"]:
                for instance in reservation["Instances"]:
                    instance_id = instance["InstanceId"]
                    state = instance["State"]["Name"]
                    instance_type = instance["InstanceType"]
                    tenancy = instance.get("Placement", {}).get("Tenancy", "shared")
                    virtualization_type = instance.get("VirtualizationType", "hvm")
                    ebs_optimized = instance.get("EbsOptimized", False)
                    processor = instance.get("ProcessorInfo", "Unknown")
                    tags = {tag["Key"]: tag["Value"] for tag in instance.get("Tags", [])}

                    # Get CPU utilization for the last 7 days
                    end_time = datetime.utcnow()
                    start_time = end_time - timedelta(days=7)

                    cloudwatch = boto3.client(
                        "cloudwatch",
                        aws_access_key_id=credentials["aws_access_key_id"],
                        aws_secret_access_key=credentials["aws_secret_access_key"],
                        region_name=region,
                    )

                    response = cloudwatch.get_metric_statistics(
                        Namespace="AWS/EC2",
                        MetricName="CPUUtilization",
                        Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=3600,
                        Statistics=["Average"],
                    )
                    avg_cpu_utilization = sum(dp["Average"] for dp in response["Datapoints"]) / len(response["Datapoints"]) if response["Datapoints"] else 0.0
                    all_instances.append(
                        {
                            "instance_id": instance_id,
                            "state": state,
                            "avg_cpu_utilization": avg_cpu_utilization,
                            "region": region,
                            "instance_type": instance_type,
                            "tenancy": tenancy,
                            "virtualization_type": virtualization_type,
                            "ebs_optimized": ebs_optimized,
                            "processor": processor,
                            "tags": tags,
                        }
                    )

            eip_filters = []

            # Create EIP filters if tags are provided, otherwise gather all EIPs
            if credentials["eip_tags"]:
                eip_tags = tag_string_to_dict(credentials["eip_tags"])
                for key, value in eip_tags.items():
                    eip_filters.append({"Name": f"tag:{key}", "Values": [value]})
                eips = regional_ec2.describe_addresses(Filters=eip_filters)["Addresses"]
            else:
                eips = regional_ec2.describe_addresses()["Addresses"]

            # Gather Elastic IPs
            for eip in eips:
                all_eips.append(
                    {
                        "public_ip": eip["PublicIp"],
                        "association_id": eip.get("AssociationId", ""),
                        "domain": eip["Domain"],
                        "region": region,
                    }
                )

            # Create snapshot filters if tags are provided, otherwise gather all snapshots
            snapshot_filters = []
            if credentials.get("volume_tags"):
                tags = tag_string_to_dict(credentials["volume_tags"])
                for key, value in tags.items():
                    snapshot_filters.append({"Name": f"tag:{key}", "Values": [value]})

            # Gather snapshots
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

        # Start threads for each region
        for region in regions:
            thread = threading.Thread(target=process_region, args=(region,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to finish
        for thread in threads:
            thread.join()

        # Format gathered data for the Rego system
        internal = {
            "aws_ec2": all_volumes,
            "aws_ec2_instances": all_instances,
            "aws_ec2_eips": all_eips,
            "aws_ec2_snapshots": all_snapshots,
        }
        rego_ready_data = {
            "input": {
                "volumes": internal.get("aws_ec2", []),
                "instances": internal.get("aws_ec2_instances", []),
                "eips": internal.get("aws_ec2_eips", []),
                "snapshots": internal.get("aws_ec2_snapshots", []),
            }
        }

        # Return the result in a standardized format
        item = Result(
            relates_to="ec2",
            result_name="ec2_data",
            result_description="Gathered data related to EC2 instances, volumes, and Elastic IPs.",
            formatted="",
            details=rego_ready_data,
        )
        return item
    