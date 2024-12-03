
# Inactive Load Balancers

## Overview

The Inactive Load Balancers check identifies load balancers that are inactive.

## Key Features

- **AWS ELB Integration**: Fetches and processes data from AWS ELB.
- **Inactive Resource Identification**: Identifies load balancers that are inactive.
- **Cost Savings Recommendations**: Recommends decommissioning inactive load balancers to save costs.

## Configuration Parameters

### AWS Configuration

- **aws_access_key_id**: AWS access key ID.
- **aws_secret_access_key**: AWS secret access key.
- **aws_region**: AWS region.

### Check Configuration

- **period**: 86400 (seconds)
- **inactive_threshold**: 30 (days)

## Example Configuration

```yaml
aws_access_key_id: your_access_key_id
aws_secret_access_key: your_secret_access_key
aws_region: your_aws_region
```