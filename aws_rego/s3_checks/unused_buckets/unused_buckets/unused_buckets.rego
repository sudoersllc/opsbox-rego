package aws_rego.s3_checks.unused_buckets.unused_buckets

import rego.v1

# Define the threshold for an unused bucket (1 year in seconds)
unused_threshold := 31536000 # 365 days * 24 hours * 60 minutes * 60 seconds

# Rule to identify unused buckets
is_unused_bucket(bucket, unused_threshold) if {
	bucket.last_modified != null # Ensure last_modified is not null
	time_diff := input.current_time - bucket.last_modified
	time_diff > unused_threshold
}

# Collect all unused buckets
buckets := [bucket | some bucket in input.buckets; is_unused_bucket(bucket, unused_threshold)]

# Output details of unused buckets
details := {"unused_buckets": buckets}
