# OpsBox Rego Checks for AWS Route 53

This module contains a Rego check plugin related to AWS's Route 53 service:

- **Empty Route 53 Hosted Zones (`empty_zones`)**

---

## Plugin Description

### Empty Route 53 Hosted Zones Plugin (`empty_zones`)
Identifies Route 53 hosted zones with no DNS records to optimize DNS management by pinpointing zones that can be deleted or reviewed.

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

To access more info about the check, install `mkdocs` and run `mkdocs serve` at the root of the package directory.

This will pull up a webpage with more complete documentation.