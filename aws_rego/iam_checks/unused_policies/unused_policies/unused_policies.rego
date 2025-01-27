package aws_rego.iam_checks.unused_policies.unused_policies

import rego.v1

# Identify policies with zero attachments
# Output only the unused policies

allow if {
policy |
	some policy in input.iam_policies
	policy.attachment_count == input.iam_unused_attachment_threshold
}

details := [policy | some policy in input.iam_policies; policy.attachment_count == input.iam_unused_attachment_threshold]
