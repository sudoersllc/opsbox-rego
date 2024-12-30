# OpsBox Rego Checks for AWS RDS

This package contains various Rego check plugins related to AWS's Relational Database Service (RDS), including:

- **RDS Idle Instances (`rds_idle`)**
- **Scaling Down RDS Instances (`scaling_down`)**
- **Empty Storage RDS Instances (`empty_storage`)**
- **Old Snapshots (`old_snapshots`)**

---

## Plugin Descriptions

### RDS Idle Instances Plugin (`rds_idle`)
Identifies idle RDS instances based on low CPU utilization or minimal connections, offering recommendations to stop or terminate them to reduce costs.

### Scaling Down RDS Instances Plugin (`scaling_down`)
Optimizes resource usage by identifying underutilized RDS instances and recommending scaling down to better match current workloads.

### Empty Storage RDS Instances Plugin (`empty_storage`)
Detects RDS instances with unutilized storage, offering opportunities to resize or terminate them to optimize storage usage and reduce costs.

### Old Snapshots Plugin (`old_snapshots`)
Finds outdated RDS snapshots that are no longer needed, providing recommendations to delete them to save on storage costs.

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