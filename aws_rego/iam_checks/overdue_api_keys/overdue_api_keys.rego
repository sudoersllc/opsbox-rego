package aws_rego.iam_checks.overdue_api_keys.overdue_api_keys

import rego.v1

# Filter overdue API keys
api_keys := [
user |
	some user in input.credential_report
	user.access_key_2_active == "true"
	key_last_rotated_ns := time.parse_rfc3339_ns(user.access_key_2_last_rotated)
	key_last_rotated_ns < input.iam_overdue_key_date_threshold
]

# Allow if there are overdue API keys
allow if count(api_keys) > 0

# Combine results into a single report
details := {"overdue_api_keys": api_keys}
