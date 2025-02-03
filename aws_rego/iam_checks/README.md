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