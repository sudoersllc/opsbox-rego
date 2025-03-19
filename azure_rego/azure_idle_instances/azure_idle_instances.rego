package azure_rego.vm_checks.idle_vms.idle_vms

import rego.v1

details := [ vm |
    some vm in input.vms;
    vm.avg_cpu_utilization < input.azure_vm_cpu_idle_threshold;
    vm.power_state == "running"
]
