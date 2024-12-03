# Storage Class Usage Plugin

## Overview

The Storage Class Usage Plugin identifies S3 buckets using specific storage classes (e.g., GLACIER, STANDARD), helping to optimize storage costs by recommending appropriate storage classes based on usage patterns.

## Key Features

- **AWS S3 Integration**: Fetches and processes data from AWS S3.
- **Cost Savings Recommendations**: Identifies buckets that can benefit from different storage classes to save costs.
- **Performance and Security Insights**: Provides detailed analysis on performance and security metrics.

## Configuration Parameters

### AWS Configuration

- **aws_access_key_id**: AWS access key ID.
- **aws_secret_access_key**: AWS secret access key.
- **aws_region**: AWS region.

### Plugin Specific Configuration

- **storage_classes**: List of storage classes to check. Default: `["GLACIER", "STANDARD"]`.

## Example Configuration

```yaml
aws_access_key_id: your_access_key_id
aws_secret_access_key: your_secret_access_key
aws_region: your_aws_region
```