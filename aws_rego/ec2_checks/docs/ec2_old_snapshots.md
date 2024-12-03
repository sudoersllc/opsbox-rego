# Old EC2 Snapshots Plugin

## Overview

The Old EC2 Snapshots Plugin identifies EC2 snapshots that are older than a specified period, helping to optimize storage costs by identifying snapshots that can be deleted or archived.

## Key Features

- **AWS EC2 Integration**: Fetches and processes data from AWS EC2.
- **Cost Savings Recommendations**: Identifies old snapshots that can be deleted or archived to save costs.
- **Detailed Analysis**: Provides detailed information on old EC2 snapshots.

## Configuration Parameters

### AWS Configuration

- **aws_access_key_id**: AWS access key ID.
- **aws_secret_access_key**: AWS secret access key.
- **aws_region**: AWS region.

## Example Configuration

```yaml
aws_access_key_id: your_access_key_id
aws_secret_access_key: your_secret_access_key
aws_region: your_aws_region
```