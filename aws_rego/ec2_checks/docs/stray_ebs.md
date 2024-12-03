# Stray EBS Volumes Plugin

## Overview

The Stray EBS Volumes Plugin identifies EBS volumes that are not attached to any instances, helping to reduce costs by deleting unused volumes.

## Key Features

- **AWS EC2 Integration**: Fetches and processes data from AWS EC2.
- **Cost Savings Recommendations**: Identifies EBS volumes that can be deleted to save costs.
- **Performance and Security Insights**: Provides detailed analysis on performance and security metrics.

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