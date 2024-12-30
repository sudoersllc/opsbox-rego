# OpsBox Rego Checks for AWS S3

This module contains various Rego check plugins related to AWS's Simple Storage Service (S3), including:

- **Unused Buckets (`unused_buckets`)**
- **Object Last Modified (`object_last_modified`)**
- **Storage Class Usage (`storage_class_usage`)**

---

## Plugin Descriptions

### Unused Buckets Plugin (`unused_buckets`)
Identifies S3 buckets that have not been accessed or modified for a specified period, providing recommendations to delete or archive them to optimize storage costs.

### Object Last Modified Plugin (`object_last_modified`)
Detects S3 objects that have not been modified for a specified period, offering opportunities to archive or delete these objects to reduce storage costs.

### Storage Class Usage Plugin (`storage_class_usage`)
Analyzes the storage classes used in S3 buckets and recommends cost-saving changes by optimizing storage class usage based on access patterns.

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