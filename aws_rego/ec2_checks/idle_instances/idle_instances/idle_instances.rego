package aws_rego.ec2_checks.idle_instances.idle_instances

import rego.v1

details := [instance | some instance in input.instances; instance.avg_cpu_utilization < 1; instance.state = "running"]
