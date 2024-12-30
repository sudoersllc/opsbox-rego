package aws.cost.console_access

# Find users with console access enabled
users_with_console_access[user] {
    user := input.credential_report[_]
    user.password_enabled == "true"
}

# Output only users with console access
details := {
    "users_with_console_access": [user | user := users_with_console_access[_]]
}
