package aws.cost.idle_instances

default allow = false

allow {
    instance := input.instances[_]
    instance.state == "running"
    instance.avg_cpu_utilization < 5  # Threshold for low CPU utilization
}

details := [instance | instance := input.instances[_]; instance.state == "running"; instance.avg_cpu_utilization < 5]