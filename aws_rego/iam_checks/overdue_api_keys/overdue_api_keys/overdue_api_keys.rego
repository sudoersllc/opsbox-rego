package aws_rego.iam_checks.overdue_api_keys.overdue_api_keys

import rego.v1

# Threshold for API key rotation (90 days)
rotation_threshold_days := 90

# Get the current time in nanoseconds
current_time_ns := time.now_ns()

# Calculate the threshold date in nanoseconds
rotation_threshold_ns := current_time_ns - (rotation_threshold_days * 86400 * 1000000000)

# Filter overdue API keys
api_keys := [
    user |
    some user in input.credential_report
    user.access_key_2_active == "true"
    key_last_rotated_ns := time.parse_rfc3339_ns(user.access_key_2_last_rotated)
    key_last_rotated_ns < rotation_threshold_ns
]

# Allow if there are overdue API keys

# Combine results into a single report
details := {"overdue_api_keys": overdue_api_keys}
