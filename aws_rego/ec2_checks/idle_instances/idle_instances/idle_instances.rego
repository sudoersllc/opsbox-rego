package aws_rego.ec2_checks.idle_instances.idle_instances

import rego.v1

default allow := false

details := [instance | some instance in input.instances; "running" in instance.state; instance.avg_cpu_utilization < 5]
