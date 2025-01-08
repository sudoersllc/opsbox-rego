package aws_rego.s3_checks.storage_class_usage.storage_class_usage

import rego.v1

# Check if the bucket is in GLACIER or STANDARD_IA storage class
is_glacier_or_standard_ia(bucket) if {
	"GLACIER" in bucket.storage_class
}

is_glacier_or_standard_ia(bucket) if {
	"STANDARD" in bucket.storage_class
}

# Count buckets with GLACIER or STANDARD_IA storage class
count_glacier_or_standard_ia := count([bucket | some bucket in input.buckets[_]; is_glacier_or_standard_ia(bucket)])

# Total number of buckets
total_buckets := count(input.buckets)

# Calculate the percentage
percentage_glacier_or_standard_ia := (100 * count_glacier_or_standard_ia) / total_buckets

# Define the policy to check if 70% or more buckets are in GLACIER or STANDARD_IA
allow if {
	percentage_glacier_or_standard_ia >= 70
}

# Output details of the buckets
glacier_or_standard_ia_buckets := [bucket | some bucket in input.buckets[_]; is_glacier_or_standard_ia(bucket)]

details := {
	"percentage_glacier_or_standard_ia": percentage_glacier_or_standard_ia,
	"glacier_or_standard_ia_buckets": glacier_or_standard_ia_buckets,
}
