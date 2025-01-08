package aws_rego.rds_checks.rds_old_snapshots.rds_old_snapshots

import rego.v1

# Identifying underutilized RDS instances with CPU utilization below 10%

gather_old_snapshots contains snapshot if {
instance |
	some instance in input.rds_snapshots[_]
	snapshot_date := time.parse_rfc3339_ns(instance.SnapshotCreateTime)
	current_time := time.parse_rfc3339_ns(input.date)
	one_year_ns := (((365 * 24) * 60) * 60) * 1000000000

	age_ns := current_time - snapshot_date
	age_ns > one_year_ns
}

# Combine results into a single report
details := {"rds_old_snapshots": [snapshot | snapshot := gather_old_snapshots[_]]}
