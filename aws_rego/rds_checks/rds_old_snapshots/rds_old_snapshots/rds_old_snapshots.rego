package aws_rego.rds_checks.rds_old_snapshots.rds_old_snapshots

import rego.v1

# Get the current time in nanoseconds
current_time_ns := time.now_ns()

# Calculate the threshold date as 1 year (365 days) before the current date
one_year_ago_ns := time.add_date(current_time_ns, -1, 0, 0) # Subtract 1 year

# Flatten the nested list of snapshots
flattened_snapshots := [snapshot |
	some sublist in input.rds_snapshots
	some snapshot in sublist
]

# Filter snapshots older than the threshold date
old_snapshots := [
snapshot |
	some snapshot in flattened_snapshots
	snapshot_create_ns := time.parse_rfc3339_ns(snapshot.SnapshotCreateTime)
	snapshot_create_ns < one_year_ago_ns
]

# Allow if there are old snapshots
allow if count(old_snapshots) > 0

# Combine results into a single report
details := {"rds_old_snapshots": old_snapshots}
