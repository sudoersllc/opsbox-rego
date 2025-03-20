from pathlib import Path
import pytest
import threading
from datetime import datetime, timedelta
from pydantic import BaseModel
from loguru import logger

# Import the provider and Result from your codebase
from azure_providers.vm.vm_provider.azure_vm_provider import AzureVMProvider # Adjust this import as needed
from opsbox import Result

# --- Fake Azure Objects ---

class FakeHardwareProfile:
    def __init__(self, vm_size):
        self.vm_size = vm_size

class FakeVM:
    def __init__(self, id, name, location, tags, vm_size):
        self.id = id
        self.name = name
        self.location = location
        self.tags = tags
        self.hardware_profile = FakeHardwareProfile(vm_size)

class FakeDisk:
    def __init__(self, id, name, location, disk_size_gb, tags):
        self.id = id
        self.name = name
        self.location = location
        self.disk_size_gb = disk_size_gb
        self.tags = tags

class FakeSnapshot:
    def __init__(self, id, name, location, disk_size_gb, provisioning_state, tags):
        self.id = id
        self.name = name
        self.location = location
        self.disk_size_gb = disk_size_gb
        self.provisioning_state = provisioning_state
        self.tags = tags

class FakePublicIP:
    def __init__(self, ip_address, name, location, allocation_method, tags):
        self.ip_address = ip_address
        self.name = name
        self.location = location
        self.public_ip_allocation_method = allocation_method
        self.tags = tags

# --- Fake Metrics Data ---

class FakeData:
    def __init__(self, average):
        self.average = average

class FakeTimeSeries:
    def __init__(self, data):
        self.data = data

class FakeMetric:
    def __init__(self, timeseries):
        self.timeseries = timeseries

class FakeMetricsResponse:
    def __init__(self, value):
        self.value = value

# --- Fake Azure Clients ---

class FakeComputeClient:
    def __init__(self, vms, disks, snapshots):
        self._vms = vms
        self._disks = disks
        self._snapshots = snapshots

    def virtual_machines(self):
        # Dummy attribute to mimic the Azure SDK attribute access
        pass

    def disks(self):
        pass

    def snapshots(self):
        pass

    @property
    def virtual_machines(self):
        class VMOperations:
            def __init__(self, vms):
                self._vms = vms

            def list(self, resource_group):
                # In a real test, you might filter by resource_group
                return self._vms

            def list_all(self):
                return self._vms

        return VMOperations(self._vms)

    @property
    def disks(self):
        class DiskOperations:
            def __init__(self, disks):
                self._disks = disks

            def list_by_resource_group(self, resource_group):
                return self._disks

            def list(self):
                return self._disks

        return DiskOperations(self._disks)

    @property
    def snapshots(self):
        class SnapshotOperations:
            def __init__(self, snapshots):
                self._snapshots = snapshots

            def list_by_resource_group(self, resource_group):
                return self._snapshots

            def list(self):
                return self._snapshots

        return SnapshotOperations(self._snapshots)

class FakeNetworkClient:
    def __init__(self, public_ips):
        self._public_ips = public_ips

    @property
    def public_ip_addresses(self):
        class PublicIPOperations:
            def __init__(self, public_ips):
                self._public_ips = public_ips

            def list(self, resource_group):
                return self._public_ips

            def list_all(self):
                return self._public_ips

        return PublicIPOperations(self._public_ips)

class FakeMonitorClient:
    def __init__(self, avg_cpu):
        self.avg_cpu = avg_cpu
        # Ensure that monitor_client.metrics.list(...) works by
        # making 'metrics' reference an object that has a 'list' method.
        self.metrics = self

    def list(self, resource_uri, timespan, interval, metricnames, aggregation):
        # Create a fake metrics response with one metric having a single timeseries
        fake_data = FakeData(average=self.avg_cpu)
        fake_timeseries = FakeTimeSeries(data=[fake_data])
        fake_metric = FakeMetric(timeseries=[fake_timeseries])
        return FakeMetricsResponse(value=[fake_metric])

# --- Test Function ---

def test_azure_vm_provider_gather_data(monkeypatch):
    """
    Test the AzureVMProvider.gather_data method.
    This test creates fake Azure resources and metrics data, substitutes the Azure SDK clients,
    and asserts the result structure.
    """

    # Disable logging for test clarity
    logger.remove()
    logger.add(lambda msg: None)

    # Create fake resources
    fake_vm = FakeVM(
        id="vm_1",
        name="test-vm",
        location="eastus",
        tags={"env": "test"},
        vm_size="Standard_DS1_v2",
    )
    fake_disk = FakeDisk(
        id="disk_1",
        name="test-disk",
        location="eastus",
        disk_size_gb=128,
        tags={"env": "test"},
    )
    fake_snapshot = FakeSnapshot(
        id="snap_1",
        name="test-snapshot",
        location="eastus",
        disk_size_gb=128,
        provisioning_state="Succeeded",
        tags={"env": "test"},
    )
    fake_public_ip = FakePublicIP(
        ip_address="1.2.3.4",
        name="test-ip",
        location="eastus",
        allocation_method="Static",
        tags={"env": "test"},
    )

    # Create fake client instances with our fake resources
    fake_compute_client = FakeComputeClient(
        vms=[fake_vm],
        disks=[fake_disk],
        snapshots=[fake_snapshot],
    )
    fake_network_client = FakeNetworkClient(
        public_ips=[fake_public_ip],
    )
    fake_monitor_client = FakeMonitorClient(avg_cpu=55.0)

    # Monkeypatch the Azure SDK client constructors and DefaultAzureCredential
    def fake_default_credential():
        return None
    
    ap = AzureVMProvider()
    ap.compute_client = fake_compute_client
    ap.network_client = fake_network_client
    ap.monitor_client = fake_monitor_client
    ap.credential = fake_default_credential

    # Create a dummy config model using Pydantic
    class MockAzureConfig(BaseModel):
        azure_subscription_id: str
        azure_resource_group: str | None = "test-rg"
        azure_locations: str | None = "eastus"
        vm_tags: str | None = '{"env": "test"}'
        disk_tags: str | None = '{"env": "test"}'
        snapshot_tags: str | None = '{"env": "test"}'
        public_ip_tags: str | None = '{"env": "test"}'

    credentials = MockAzureConfig(
        azure_subscription_id="fake-subscription-id",
        azure_resource_group="test-rg",
        azure_locations="eastus",
        vm_tags='{"env": "test"}',
        disk_tags='{"env": "test"}',
        snapshot_tags='{"env": "test"}',
        public_ip_tags='{"env": "test"}',
    )

    # Instantiate the provider and set credentials
    provider = ap
    provider.set_data(credentials)

    # Invoke gather_data
    result = provider.gather_data()

    # Optionally output JSON to a file (using tmp_path)
    json_output = True
    if json_output:
        output_file = Path(".") / "azure_vm_test_data.json"
        with output_file.open("w") as f:
            import json

            json.dump(result.model_dump()["details"]["input"], f, indent=4)

    # Assertions
    assert isinstance(result, Result)
    assert result.relates_to == "azure_vm"
    assert result.result_name == "azure_vm_data"
    details = result.details["input"]

    # Verify structure of gathered data
    assert "vms" in details
    assert "disks" in details
    assert "snapshots" in details
    assert "public_ips" in details

    # Verify VM data
    vms = details["vms"]
    assert len(vms) == 1
    vm = vms[0]
    assert vm["name"] == "test-vm"
    assert vm["location"] == "eastus"
    assert vm["vm_size"] == "Standard_DS1_v2"
    # The fake monitor returned an average of 55.0
    assert vm["avg_cpu_utilization"] == 55.0

    # Verify Disk data
    disks = details["disks"]
    assert len(disks) == 1
    disk = disks[0]
    assert disk["name"] == "test-disk"
    assert disk["size_gb"] == 128

    # Verify Snapshot data
    snapshots = details["snapshots"]
    assert len(snapshots) == 1
    snapshot = snapshots[0]
    assert snapshot["name"] == "test-snapshot"
    assert snapshot["provisioning_state"] == "Succeeded"

    # Verify Public IP data
    public_ips = details["public_ips"]
    assert len(public_ips) == 1
    public_ip = public_ips[0]
    assert public_ip["name"] == "test-ip"
    assert public_ip["ip_address"] == "1.2.3.4"
