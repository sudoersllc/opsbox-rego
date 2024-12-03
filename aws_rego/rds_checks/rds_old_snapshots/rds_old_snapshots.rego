package aws.cost.rds_old_snapshots
# Identifying underutilized RDS instances with CPU utilization below 10%

gather_old_snapshots[snapshot] {
    instance := input.rds_snapshots[_]
    snapshot_date := time.parse_rfc3339_ns(instance.SnapshotCreateTime)
    current_time := time.parse_rfc3339_ns(input.date)
    one_year_ns := 365 * 24 * 60 * 60 * 1000000000
    
    age_ns := current_time - snapshot_date
    age_ns > one_year_ns

    snapshot := instance
}

# Combine results into a single report
details := {
    "rds_old_snapshots": [snapshot | snapshot := gather_old_snapshots[_]]
}
