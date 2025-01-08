package aws_rego.iam_checks.unused_policies.unused_policies

import rego.v1

# Identify policies with zero attachments
# Output only the unused policies

allow if {
	policy |
		some policy in input.policies
		policy.attachment_count == 0
}
details := [policy | some policy in input.policies; policy.attachment_count == 0]
