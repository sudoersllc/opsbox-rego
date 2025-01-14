package aws_rego.iam_checks.mfa_enabled.mfa_enabled

import rego.v1

# Find users without MFA enabled

allow if {
user |
	some user in input.credential_report
	user.mfa_active == "false"
}

# Output only users without MFA
details := [user | some user in input.credential_report; user.mfa_active == "false"]
