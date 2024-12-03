package aws.cost.storage_class_usage

# Check if the bucket is in GLACIER or STANDARD_IA storage class
is_glacier_or_standard_ia(bucket) {
    bucket.storage_class == "GLACIER"
} {
    bucket.storage_class == "STANDARD"
}

# Count buckets with GLACIER or STANDARD_IA storage class
count_glacier_or_standard_ia = count([bucket | bucket := input.buckets[_]; is_glacier_or_standard_ia(bucket)])

# Total number of buckets
total_buckets = count(input.buckets)

# Calculate the percentage
percentage_glacier_or_standard_ia = 100 * count_glacier_or_standard_ia / total_buckets

# Define the policy to check if 70% or more buckets are in GLACIER or STANDARD_IA
allow {
    percentage_glacier_or_standard_ia >= 70
}

# Output details of the buckets
glacier_or_standard_ia_buckets := [bucket | bucket := input.buckets[_]; is_glacier_or_standard_ia(bucket)]

details := {
    "percentage_glacier_or_standard_ia": percentage_glacier_or_standard_ia,
    "glacier_or_standard_ia_buckets": glacier_or_standard_ia_buckets
}
