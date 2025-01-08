package aws_rego.s3_checks.unused_buckets.unused_buckets

import rego.v1

# Rule to identify unused buckets
is_unused_bucket(bucket) if {
	time_diff := input.current_time - bucket.last_modified
	time_diff > ((365 * 24) * 60) * 60
}

# Collect unused buckets
buckets_list := [bucket | some bucket in input.buckets[_]; is_unused_bucket(bucket)]

# Collect details of all unused buckets
details := {"unused_buckets": buckets_list}
