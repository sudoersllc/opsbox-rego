package aws.cost.unused_policies

# Identify policies with zero attachments
unused_policies[policy] {
    policy := input.iam_policies[_]
    policy.attachment_count == 0
}

# Output only the unused policies
details := {
    "unused_policies": [policy | policy := unused_policies[_]]
}

