# OpsBox Rego Checks for EC2

This package contains various Rego check plugins related to AWS's EC2 service, including:

- **Stray EBS Volumes (`stray_ebs`)**
- **Old EC2 Snapshots (`ec2_old_snapshots`)**
- **Idle Instances (`idle_instances`)**
- **Stray Instances (`stray_instances`)**
- **Unattached EIPs (`unattached_eips`)**

---

## Plugin Descriptions

### Unattached EIPs Plugin (`unattached_eips`)
Identifies Elastic IPs (EIPs) not associated with running instances to help reduce costs by releasing unused EIPs. Offers cost-saving recommendations and detailed performance and security analysis.

### Old EC2 Snapshots Plugin (`ec2_old_snapshots`)
Finds EC2 snapshots older than a specified period to optimize storage costs by identifying snapshots for deletion or archiving. Provides detailed information on old snapshots.

### Idle Instances Plugin (`idle_instances`)
Detects EC2 instances with low utilization to reduce costs by stopping or terminating idle instances. Includes performance and security insights for better resource optimization.

### Stray EBS Volumes Plugin (`stray_ebs`)
Identifies unused EBS volumes that are not attached to any instances, enabling cost savings by deleting these volumes. Includes insights into performance and security metrics.

### Stray Instances Plugin (`stray_instances`)
Finds EC2 instances not associated with any specific workload or application, reducing costs by terminating unused instances. Provides detailed analysis for efficient resource management.

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

To access more info about each check, install mkdocs and run `mkdocs serve` at the root of the package directory

This will pull up a webpage with more complete documentation.