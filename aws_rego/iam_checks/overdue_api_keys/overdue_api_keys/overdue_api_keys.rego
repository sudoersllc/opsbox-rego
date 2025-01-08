package aws_rego.iam_checks.overdue_api_keys.overdue_api_keys

import rego.v1

# Threshold for API key rotation (90 days)
rotation_threshold_days := 90

# Find overdue API keys

api_keys contains user if {
user |
	some user in input.credential_report[_]
	"true" in user.access_key_2_active
	days_since_rotation(user.access_key_2_last_rotated) > rotation_threshold_days
}

# Calculate days since a given date
days_since_rotation(date) := diff if {
	now := time.now_ns() / 1000000000 # Current time in seconds
	rotated := time.parse_rfc3339_ns(date) / 1000000000 # Last rotated time in seconds
	diff := (now - rotated) / 86400 # Convert difference to days
}

# Output only overdue API keys
details := {"overdue_api_keys": [user | user := api_keys[_]]}
