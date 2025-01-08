package aws_rego.iam_checks.mfa_enabled.mfa_enabled

import rego.v1

# Find users without MFA enabled
users_without_mfa contains user if {
user |
	some user in input.credential_report[_]
	"false" in user.mfa_active
}

# Output only users without MFA
details := {"users_without_mfa": [user | user := users_without_mfa[_]]}
