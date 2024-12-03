# Unused Buckets Plugin

## Overview

The Unused Buckets Plugin identifies S3 buckets that have not been accessed or modified for a specified period, helping to optimize storage costs by identifying buckets that can be deleted or archived.

## Key Features

- **AWS S3 Integration**: Fetches and processes data from AWS S3.
- **Cost Savings Recommendations**: Identifies unused buckets that can be deleted or archived to save costs.
- **Performance and Security Insights**: Provides detailed analysis on performance and security metrics.

## Configuration Parameters

### AWS Configuration

- **aws_access_key_id**: AWS access key ID.
- **aws_secret_access_key**: AWS secret access key.
- **aws_region**: AWS region.

### Plugin Specific Configuration

- **unused_period**: The period of inactivity to consider a bucket as unused. Default: 1 year.

## Example Configuration

```yaml
aws_access_key_id: your_access_key_id
aws_secret_access_key: your_secret_access_key
aws_region: your_aws_region
```