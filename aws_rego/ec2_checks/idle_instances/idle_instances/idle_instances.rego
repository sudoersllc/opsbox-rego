package aws_rego.ec2_checks.idle_instances.idle_instances

import rego.v1

allow if {
instance |
	some instance in input.instances
	instance.avg_cpu_utilization < input.ec2_cpu_idle_threshold # Check if avg_cpu_utilization is less than 1
	instance.state == "running" # Check if state is running
}

details := [instance | some instance in input.instances; instance.avg_cpu_utilization < input.ec2_cpu_idle_threshold; instance.state = "running"]
