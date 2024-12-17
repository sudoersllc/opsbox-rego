package aws.cost.overdue_api_keys

# Threshold for API key rotation (90 days)
rotation_threshold_days := 90

# Find overdue API keys
overdue_api_keys[user] {
    user := input.credential_report[_]
    user.access_key_1_active == "true"
    days_since_rotation(user.access_key_1_last_rotated) > rotation_threshold_days
} {
    user := input.credential_report[_]
    user.access_key_2_active == "true"
    days_since_rotation(user.access_key_2_last_rotated) > rotation_threshold_days
}

# Calculate days since a given date
days_since_rotation(date) = diff {
    now := time.now_ns() / 1000000000  # Current time in seconds
    rotated := time.parse_rfc3339_ns(date) / 1000000000  # Last rotated time in seconds
    diff := (now - rotated) / 86400  # Convert difference to days
}

# Output only overdue API keys
details := {
    "overdue_api_keys": [user | user := overdue_api_keys[_]]
}
