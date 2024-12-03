# Empty Storage Plugin

## Overview

The Empty Storage Plugin identifies RDS instances with empty storage, helping to optimize storage usage and reduce costs by identifying instances that can be resized or terminated.

## Key Features

- **AWS RDS Integration**: Fetches and processes data from AWS RDS.
- **Cost Savings Recommendations**: Identifies RDS instances with empty storage that can be resized or terminated to save costs.
- **Performance and Security Insights**: Provides detailed analysis on performance and security metrics.

## Configuration Parameters

### AWS Configuration

- **aws_access_key_id**: AWS access key ID.
- **aws_secret_access_key**: AWS secret access key.
- **aws_region**: AWS region.

### Plugin Specific Configuration

- **storage_threshold**: The storage threshold (in %) that will count as unutilized (default is 40)

## Example Configuration

```yaml
aws_access_key_id: your_access_key_id
aws_secret_access_key: your_secret_access_key
aws_region: your_aws_region
```