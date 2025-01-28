package aws_rego.iam_checks.console_access.console_access

import rego.v1

# Find users with console access enabled

# Output only users with console access
details := [user | some user in input.credential_report; user.password_enabled = "true"]
