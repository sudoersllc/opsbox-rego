package aws_rego.ec2_checks.ec2_old_snapshots.ec2_old_snapshots

import rego.v1

# Get the current time in nanoseconds
current_time_ns := time.now_ns()

# Calculate the threshold date as 1 year (365 days) before the current date
one_year_ago_ns := time.add_date(current_time_ns, -1, 0, 0) # Subtract 1 year

# Filter snapshots older than the threshold date
old_snapshots := [
snapshot |
	some snapshot in input.snapshots
	snapshot_start_ns := time.parse_rfc3339_ns(snapshot.start_time)
	snapshot_start_ns < one_year_ago_ns
]


# Combine results into a single report
details := {"ec2_old_snapshots": old_snapshots}
