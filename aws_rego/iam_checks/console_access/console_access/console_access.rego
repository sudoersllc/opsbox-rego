package aws_rego.iam_checks.console_access.console_access

import rego.v1

# Find users with console access enabled
users_with_console_access contains user if {
user |
	some user in input.users
	"true" in user.password_enabled
}

# Output only users with console access
details := {"users_with_console_access": [user | user := users_with_console_access[_]]}
