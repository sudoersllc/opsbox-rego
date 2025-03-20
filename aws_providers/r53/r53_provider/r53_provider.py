from pluggy import HookimplMarker
from pydantic import BaseModel, Field
import boto3
from loguru import logger
from typing import Annotated
from opsbox import Result
import threading

# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")


class Route53Provider:
    """Plugin for gathering data related to AWS Route 53 hosted zones, DNS records, health checks."""

    @hookimpl
    def grab_config(self):
        """Return the plugin's configuration."""

        class Route53Config(BaseModel):
            """Configuration for the AWS Route 53 plugin."""

            aws_access_key_id: Annotated[
                str,
                Field(description="AWS access key ID", required=False, default=None),
            ]
            aws_secret_access_key: Annotated[
                str,
                Field(
                    description="AWS secret access key", required=False, default=None
                ),
            ]
            aws_region: Annotated[
                str | None,
                Field(description="AWS region", required=False, default=None),
            ]

        return Route53Config

    @hookimpl
    def activate(self) -> None:
        """Initialize the plugin."""
        logger.trace("Activating Route 53 plugin...")

    @hookimpl
    def set_data(self, model: type[BaseModel]) -> None:
        """Set the data for the plugin based on the model."""
        logger.trace("Setting data for Route 53 plugin...")
        self.credentials = model.model_dump()

    @hookimpl
    def gather_data(self):
        """Gathers data related to AWS Route 53 hosted zones, DNS records, health checks."""
        logger.info("Gathering data for AWS Route 53...")
        credentials = self.credentials

        # Determine regions if needed (though not used directly in the fetch)
        if credentials["aws_region"] is None:
            region_client = boto3.client(
                "ec2",
                aws_access_key_id=credentials["aws_access_key_id"],
                aws_secret_access_key=credentials["aws_secret_access_key"],
                region_name="us-west-1",
            )
            regions = [
                region["RegionName"]
                for region in region_client.describe_regions()["Regions"]
            ]
            logger.info(f"Regions: {regions}")
        else:
            regions = credentials["aws_region"].split(",")

        # Shared data structures for storing results
        hosted_zones = []
        all_records = []
        health_checks = []

        # Create a lock to ensure thread-safe updates to the shared data
        data_lock = threading.Lock()

        def fetch_route53_data():
            try:
                if (
                    credentials["aws_access_key_id"] is None
                    or credentials["aws_secret_access_key"] is None
                ):
                    route53 = boto3.client("route53")
                else:
                    route53 = boto3.client(
                        "route53",
                        aws_access_key_id=credentials["aws_access_key_id"],
                        aws_secret_access_key=credentials["aws_secret_access_key"],
                    )
            except Exception as e:
                logger.error(f"Error creating Route 53 client: {e}")
                return Result(
                    relates_to="aws_data",
                    result_name="aws_data",
                    result_description="Gathered data related to Route 53.",
                    formatted="Error creating Route 53 client.",
                    details={},
                )

            # Gather hosted zones
            paginator = route53.get_paginator("list_hosted_zones")
            for page in paginator.paginate():
                for zone in page["HostedZones"]:
                    with data_lock:
                        hosted_zones.append(
                            {
                                "id": zone["Id"],
                                "name": zone["Name"],
                                "record_count": zone["ResourceRecordSetCount"],
                                "private_zone": zone["Config"].get(
                                    "PrivateZone", False
                                ),
                            }
                        )

            # Gather DNS records for each hosted zone, filtering for A and CNAME records
            for zone in hosted_zones:
                zone_id = zone["id"]
                paginator = route53.get_paginator("list_resource_record_sets")
                for page in paginator.paginate(HostedZoneId=zone_id):
                    for record in page["ResourceRecordSets"]:
                        if record["Type"] in ["A", "CNAME"]:
                            with data_lock:
                                all_records.append(
                                    {
                                        "zone_id": zone_id,
                                        "name": record["Name"],
                                        "type": record["Type"],
                                        "ttl": record.get("TTL", None),
                                        "records": record.get("ResourceRecords", []),
                                    }
                                )

            # Gather health checks
            paginator = route53.get_paginator("list_health_checks")
            for page in paginator.paginate():
                for check in page["HealthChecks"]:
                    with data_lock:
                        health_checks.append(
                            {
                                "id": check["Id"],
                                "type": check["HealthCheckConfig"]["Type"],
                                "ip_address": check["HealthCheckConfig"].get(
                                    "IPAddress", ""
                                ),
                                "port": check["HealthCheckConfig"].get("Port", None),
                                "resource_path": check["HealthCheckConfig"].get(
                                    "ResourcePath", ""
                                ),
                                "failure_threshold": check["HealthCheckConfig"].get(
                                    "FailureThreshold", 3
                                ),
                            }
                        )

        # Start a thread to fetch Route 53 data
        route53_thread = threading.Thread(target=fetch_route53_data)
        route53_thread.start()

        # Wait for the Route 53 thread to complete
        route53_thread.join()

        # Prepare the data for Rego consumption
        rego_ready_data = {
            "input": {
                "hosted_zones": hosted_zones,
                "records": all_records,
                "health_checks": health_checks,
            }
        }
        logger.success(rego_ready_data)

        item = Result(
            relates_to="aws_data",
            result_name="aws_data",
            result_description="Gathered data related to Route 53.",
            formatted="",
            details=rego_ready_data,
        )

        return item
