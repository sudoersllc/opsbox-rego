from pluggy import HookimplMarker
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from loguru import logger
import threading
from typing import Annotated, Optional
from opsbox import Result
import json

from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.monitor import MonitorManagementClient

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
            raise ValueError("Tags provided are not in a valid JSON format.")


class AzureVMProvider:
    """Plugin for gathering data related to Azure Virtual Machines, managed disks,
    snapshots, and Public IP addresses.

    Attributes:
        credentials (dict): A dictionary containing Azure subscription and filtering details.
    """

    @hookimpl
    def grab_config(self):
        """Define and return the configuration model for the Azure VM provider.

        Returns:
            AzureConfig: The configuration model for the Azure VM provider.
        """
        class AzureConfig(BaseModel):
            """Configuration schema for the Azure VM provider.

            Attributes:
                azure_subscription_id (str): Azure subscription ID.
                azure_resource_group (str, optional): Azure resource group name.
                azure_locations (str, optional): Comma-separated list of Azure locations (regions).
                vm_tags (str, optional): Key-value tag pairs for Virtual Machines.
                disk_tags (str, optional): Key-value tag pairs for Managed Disks.
                snapshot_tags (str, optional): Key-value tag pairs for Snapshots.
                public_ip_tags (str, optional): Key-value tag pairs for Public IP addresses.
            """
            azure_subscription_id: Annotated[
                str | None,
                Field(
                    description="Azure subscription ID",
                    required=True
                )
            ]
            azure_resource_group: Annotated[
                str | None,
                Field(
                    description="Azure resource group name (optional)",
                    default=None
                )
            ]
            azure_locations: Annotated[
                str | None,
                Field(
                    description="Comma-separated Azure locations (regions) to filter resources",
                    default=None
                )
            ]
            vm_tags: Annotated[
                str | None,
                Field(
                    description="Key-value tag pairs for Virtual Machines",
                    default=None
                )
            ]
            disk_tags: Annotated[
                str | None,
                Field(
                    description="Key-value tag pairs for Managed Disks",
                    default=None
                )
            ]
            snapshot_tags: Annotated[
                str | None,
                Field(
                    description="Key-value tag pairs for Snapshots",
                    default=None
                )
            ]
            public_ip_tags: Annotated[
              str | None,
                Field(
                    description="Key-value tag pairs for Public IP addresses",
                    default=None
                )
            ]
        return AzureConfig

    @hookimpl
    def activate(self) -> None:
        """Log a trace message indicating the provider is being activated."""
        logger.trace("Activating Azure VM provider...")

    @hookimpl
    def set_data(self, model: type[BaseModel]) -> None:
        """Store the configuration from the model.

        Args:
            model (BaseModel): The configuration model for the Azure VM provider.
        """
        logger.trace("Setting data for Azure VM provider...")
        self.credentials = model.model_dump()

    @hookimpl
    def gather_data(self):
        """Gather data for Azure Virtual Machines, Managed Disks, Snapshots,
        and Public IP addresses.

        Returns:
            Result: A formatted result containing the gathered data.
        """
        logger.info("Gathering data for Azure VMs, Disks, Snapshots, and Public IPs...")
        creds = self.credentials
        subscription_id = creds["azure_subscription_id"]
        resource_group = creds.get("azure_resource_group")
        # Parse locations if provided; otherwise process all locations
        locations = None
        if creds.get("azure_locations"):
            locations = [loc.strip().lower() for loc in creds["azure_locations"].split(",")]

        # Parse tag filters if provided
        vm_tag_filter = tag_string_to_dict(creds["vm_tags"]) if creds.get("vm_tags") else None
        disk_tag_filter = tag_string_to_dict(creds["disk_tags"]) if creds.get("disk_tags") else None
        snapshot_tag_filter = tag_string_to_dict(creds["snapshot_tags"]) if creds.get("snapshot_tags") else None
        public_ip_tag_filter = tag_string_to_dict(creds["public_ip_tags"]) if creds.get("public_ip_tags") else None

        # Set time range for metrics (last 7 days)
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=7)
        timespan = f"{start_time.isoformat()}/{end_time.isoformat()}"

        # Initialize Azure credentials and clients
        credential = DefaultAzureCredential()
        compute_client = ComputeManagementClient(credential, subscription_id)
        network_client = NetworkManagementClient(credential, subscription_id)
        monitor_client = MonitorManagementClient(credential, subscription_id)

        # Containers to store gathered data
        all_vms = []
        all_disks = []
        all_snapshots = []
        all_public_ips = []

        # Lock for thread-safe updates
        data_lock = threading.Lock()

        def process_vms():
            """Gather VMs, filter them by location (if provided) and tags, and retrieve CPU metrics."""
            # List VMs either by resource group or across the subscription
            if resource_group:
                vm_list = compute_client.virtual_machines.list(resource_group)
            else:
                vm_list = compute_client.virtual_machines.list_all()

            for vm in vm_list:
                # Filter by location if locations are provided
                if locations and vm.location.lower() not in locations:
                    continue

                # Filter by VM tags if provided
                if vm_tag_filter:
                    vm_tags = vm.tags or {}
                    if not all(vm_tags.get(k) == v for k, v in vm_tag_filter.items()):
                        continue

                # Attempt to get CPU metrics from Monitor
                avg_cpu = 0.0
                try:
                    # The resource URI is the VM's ID
                    metrics_data = monitor_client.metrics.list(
                        resource_uri=vm.id,
                        timespan=timespan,
                        interval="PT1H",
                        metricnames="Percentage CPU",
                        aggregation="Average"
                    )
                    # Compute average from returned metrics (if any)
                    datapoints = []
                    for item in metrics_data.value:
                        for timeserie in item.timeseries:
                            for data in timeserie.data:
                                if data.average is not None:
                                    datapoints.append(data.average)
                    if datapoints:
                        avg_cpu = sum(datapoints) / len(datapoints)
                except Exception as e:
                    logger.error(f"Error retrieving CPU metrics for VM {vm.name}: {e}")

                with data_lock:
                    all_vms.append({
                        "vm_id": vm.id,
                        "name": vm.name,
                        "location": vm.location,
                        "vm_size": vm.hardware_profile.vm_size if vm.hardware_profile else "Unknown",
                        "avg_cpu_utilization": avg_cpu,
                        "tags": vm.tags or {},
                    })

        def process_disks():
            """Gather Managed Disks and filter by tags if provided."""
            if resource_group:
                disk_list = compute_client.disks.list_by_resource_group(resource_group)
            else:
                disk_list = compute_client.disks.list()
            for disk in disk_list:
                # Filter by disk tags if provided
                if disk_tag_filter:
                    disk_tags = disk.tags or {}
                    if not all(disk_tags.get(k) == v for k, v in disk_tag_filter.items()):
                        continue

                with data_lock:
                    all_disks.append({
                        "disk_id": disk.id,
                        "name": disk.name,
                        "location": disk.location,
                        "size_gb": disk.disk_size_gb,
                        "tags": disk.tags or {},
                    })

        def process_snapshots():
            """Gather Snapshots and filter by tags if provided."""
            if resource_group:
                snapshot_list = compute_client.snapshots.list_by_resource_group(resource_group)
            else:
                snapshot_list = compute_client.snapshots.list()
            for snapshot in snapshot_list:
                # Filter by snapshot tags if provided
                if snapshot_tag_filter:
                    snap_tags = snapshot.tags or {}
                    if not all(snap_tags.get(k) == v for k, v in snapshot_tag_filter.items()):
                        continue

                with data_lock:
                    all_snapshots.append({
                        "snapshot_id": snapshot.id,
                        "name": snapshot.name,
                        "location": snapshot.location,
                        "disk_size_gb": snapshot.disk_size_gb,
                        "provisioning_state": snapshot.provisioning_state,
                        "tags": snapshot.tags or {},
                    })

        def process_public_ips():
            """Gather Public IP addresses and filter by tags if provided."""
            if resource_group:
                ip_list = network_client.public_ip_addresses.list(resource_group)
            else:
                ip_list = network_client.public_ip_addresses.list_all()
            for ip in ip_list:
                # Filter by public IP tags if provided
                if public_ip_tag_filter:
                    ip_tags = ip.tags or {}
                    if not all(ip_tags.get(k) == v for k, v in public_ip_tag_filter.items()):
                        continue

                with data_lock:
                    all_public_ips.append({
                        "ip_address": ip.ip_address,
                        "name": ip.name,
                        "location": ip.location,
                        "allocation_method": ip.public_ip_allocation_method,
                        "tags": ip.tags or {},
                    })

        # Start threads for each resource category to parallelize work
        threads = []
        for func in [process_vms, process_disks, process_snapshots, process_public_ips]:
            thread = threading.Thread(target=func)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Format gathered data for the Rego system
        internal = {
            "azure_vms": all_vms,
            "azure_disks": all_disks,
            "azure_snapshots": all_snapshots,
            "azure_public_ips": all_public_ips,
        }
        rego_ready_data = {
            "input": {
                "vms": internal.get("azure_vms", []),
                "disks": internal.get("azure_disks", []),
                "snapshots": internal.get("azure_snapshots", []),
                "public_ips": internal.get("azure_public_ips", []),
            }
        }

        # Return the result in a standardized format
        item = Result(
            relates_to="azure_vm",
            result_name="azure_vm_data",
            result_description="Gathered data related to Azure VMs, Managed Disks, Snapshots, and Public IP addresses.",
            formatted="",
            details=rego_ready_data,
        )
        return item
