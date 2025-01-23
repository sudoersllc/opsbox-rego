package aws_rego.iam_checks.unused_policies.unused_policies

import rego.v1

# Identify policies with zero attachments
# Output only the unused policies


details := [policy | some policy in input.iam_policies; policy.attachment_count == 0]
