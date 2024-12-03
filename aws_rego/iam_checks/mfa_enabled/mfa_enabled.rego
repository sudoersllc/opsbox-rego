package aws.cost.mfa_enabled

# Find users without MFA enabled
users_without_mfa[user] {
    user := input.credential_report[_]
    user.mfa_active == "false"

}

# Output only users without MFA
details := {
    "users_without_mfa": [user | user := users_without_mfa[_]]
}