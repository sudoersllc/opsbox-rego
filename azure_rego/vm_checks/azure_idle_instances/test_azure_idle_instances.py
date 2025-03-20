import json
import os
import pathlib


def test_azure_idle_instances(rego_process):
    """Test for idle Azure VMs policy"""
    # Load rego policy
    current_dir = pathlib.Path(os.path.abspath(__file__)).parent

    # if test key does not exist in the result, the test will fail.
    # we need to add azure_vm_cpu_idle_threshold to the json file.
    write: bool = False
    test_data = os.path.join(current_dir.parent, "azure_vm_test_data.json")
    with open(test_data, "r") as file:
        data = json.load(file)
        if "azure_vm_cpu_idle_threshold" not in data:
            data["azure_vm_cpu_idle_threshold"] = 1
            write = True

    # overwrite the file
    if write:
        with open(test_data, "w") as file:
            json.dump(data, file, indent=4)

    # Load rego policy
    rego_policy = os.path.join(current_dir, "azure_idle_instances.rego")
    rego_input = os.path.join(current_dir.parent, "azure_vm_test_data.json")
    needed_keys = [
        "vm_id",
        "location",
        "power_state",
        "avg_cpu_utilization",
        "vm_size",
        "operating_system",
        "tags",
    ]
    rego_process(rego_policy, rego_input, "data.azure.vm.idle_instances", needed_keys)