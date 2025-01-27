package aws_rego.s3_checks.unused_buckets.unused_buckets

import rego.v1

# Rule to identify unused buckets
is_unused_bucket(bucket) if {
	bucket.last_modified != null # Ensure last_modified is not null
	bucket.last_modified <= input.s3_unused_bucket_date_threshold
}

# Collect all unused buckets
buckets := [bucket | some bucket in input.buckets; is_unused_bucket(bucket)]

# Output details of unused buckets
details := {"unused_buckets": buckets}
