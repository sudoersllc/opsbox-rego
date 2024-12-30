package aws.cost.unused_buckets

# Rule to identify unused buckets
is_unused_bucket(bucket) {
    time_diff := input.current_time - bucket.last_modified
    time_diff > 365 * 24 * 60 * 60
}

# Collect unused buckets
unused_buckets = [bucket | bucket := input.buckets[_]; is_unused_bucket(bucket)]

# Collect details of all unused buckets
details = {
    "unused_buckets": unused_buckets
}