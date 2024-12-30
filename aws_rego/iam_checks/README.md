# OpsBox Rego Checks for AWS IAM

This module contains various Rego check plugins related to AWS's Identity and Access Management (IAM) service, including:

- **Unused IAM Policies (`unused_policies`)**
- **Console Access (`console_access`)**
- **IAM Users Without MFA (`mfa_enabled`)**
- **Overdue API Keys (`overdue_api_keys`)**

---

## Plugin Descriptions

### Unused IAM Policies Plugin (`unused_policies`)
Identifies IAM policies with zero attachments to optimize policy management and help reduce unused resources.

### Console Access Plugin (`console_access`)
Identifies IAM users with console access enabled, offering recommendations to enhance security by limiting access to necessary users.

### IAM Users Without MFA Plugin (`mfa_enabled`)
Detects IAM users without Multi-Factor Authentication (MFA) enabled to improve account security.

### Overdue API Keys Plugin (`overdue_api_keys`)
Finds IAM API keys that are overdue, ensuring keys are rotated regularly to enhance security.

---

## Common Configuration

All plugins share the following AWS configuration:

- **aws_access_key_id**: AWS access key ID
- **aws_secret_access_key**: AWS secret access key
- **aws_region**: AWS region (optional)

```yaml
aws_access_key_id: your_access_key_id
aws_secret_access_key: your_secret_access_key
aws_region: your_aws_region
```

---

To access more info about each check, install `mkdocs` and run `mkdocs serve` at the root of the package directory.

This will pull up a webpage with more complete documentation.