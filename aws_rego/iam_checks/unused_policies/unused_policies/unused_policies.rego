package aws_rego.iam_checks.unused_policies.unused_policies

import rego.v1

# Identify policies with zero attachments
policies_list contains policy if {
policy |
	some policy in input.policies
	policy.attachment_count == 0
}

# Output only the unused policies
details := {"unused_policies": [policy | policy := policies_list[_]]}
