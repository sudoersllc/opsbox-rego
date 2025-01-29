package aws_rego.s3_checks.storage_class_usage.storage_class_usage

import rego.v1


# Check if the bucket is in GLACIER or STANDARD_IA storage class
is_glacier_or_standard_ia(bucket) if {
	bucket.storage_class == "GLACIER"
} else if {
	bucket.storage_class == "STANDARD_IA"
}

# Check if the bucket is stale
is_stale(bucket) if {
	bucket.last_modified != null
	bucket.last_modified < input.s3_stale_bucket_date_threshold
}

# Check if the bucket has a MIXED storage class
is_mixed_storage(bucket) if {
	bucket.storage_class == "MIXED"
}

# Count buckets with GLACIER or STANDARD_IA storage class
count_glacier_or_standard_ia := count([bucket | some bucket in input.buckets; is_glacier_or_standard_ia(bucket)])

# Count stale buckets
count_stale := count([bucket | some bucket in input.buckets; is_stale(bucket)])

# Count buckets with MIXED storage class
count_mixed := count([bucket | some bucket in input.buckets; is_mixed_storage(bucket)])

# Total number of buckets
total_buckets := count(input.buckets)

# Calculate percentages
percentage_glacier_or_standard_ia := (100 * count_glacier_or_standard_ia) / total_buckets

percentage_stale := (100 * count_stale) / total_buckets

percentage_mixed := (100 * count_mixed) / total_buckets

# Output details
details := {
	"total_buckets": total_buckets,
	"count_glacier_or_standard_ia": count_glacier_or_standard_ia,
	"count_stale": count_stale,
	"count_mixed": count_mixed,
	"percentage_glacier_or_standard_ia": percentage_glacier_or_standard_ia,
	"percentage_stale": percentage_stale,
	"percentage_mixed": percentage_mixed,
	"stale_buckets": [bucket | some bucket in input.buckets; is_stale(bucket)],
	"mixed_storage_buckets": [bucket | some bucket in input.buckets; is_mixed_storage(bucket)],
	"glacier_or_standard_ia_buckets": [bucket | some bucket in input.buckets; is_glacier_or_standard_ia(bucket)],
}

# Policy check: Ensure at least 70% of buckets are in GLACIER or STANDARD_IA
allow_glacier_or_standard_ia if {
	percentage_glacier_or_standard_ia >= 70
}

# Policy check: Flag if more than 20% of buckets are stale
flag_stale_buckets if {
	percentage_stale > 20
}

# Policy check: Ensure no buckets have MIXED storage class
allow_no_mixed_storage if {
	count_mixed == 0
}
