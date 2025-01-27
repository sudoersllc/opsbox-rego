package aws_rego.ec2_checks.ec2_old_snapshots.ec2_old_snapshots

import rego.v1


# Filter snapshots older than the threshold date
old_snapshots := [
snapshot |
	some snapshot in input.snapshots
	snapshot_start_ns := time.parse_rfc3339_ns(snapshot.start_time)
	snapshot_start_ns < input.ec2_snapshot_old_threshold
]

allow if count(old_snapshots) > 0

# Combine results into a single report
details := {"ec2_old_snapshots": old_snapshots}
