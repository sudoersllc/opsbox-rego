# Old Snapshots Plugin

## Overview

The Old Snapshots Plugin identifies old RDS snapshots that are no longer needed, helping to reduce storage costs by deleting outdated snapshots.

## Key Features

- **AWS RDS Integration**: Fetches and processes data from AWS RDS.
- **Cost Savings Recommendations**: Identifies old snapshots that can be deleted to save storage costs.
- **Performance and Security Insights**: Provides detailed analysis on performance and security metrics.

## Configuration Parameters

### AWS Configuration

- **aws_access_key_id**: AWS access key ID.
- **aws_secret_access_key**: AWS secret access key.
- **aws_region**: AWS region.

### Plugin Specific Defaults

- **snapshot_age_threshold**: The age threshold to consider. Default is 1 year.

## Example Configuration

```yaml
aws_access_key_id: your_access_key_id
aws_secret_access_key: your_secret_access_key
aws_region: your_aws_region
```