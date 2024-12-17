package aws.cost.ec2_old_snapshots

gather_old_snapshots[snapshot] {
    instance := input.snapshots[_]
    snapshot := instance
}

# Combine results into a single report
details := {
    "ec2_old_snapshots": [snapshot | snapshot := gather_old_snapshots[_]]
}
