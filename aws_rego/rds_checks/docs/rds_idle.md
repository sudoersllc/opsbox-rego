# RDS Idle Plugin

## Overview

The RDS Idle Plugin identifies idle RDS instances, helping to optimize resource usage and reduce costs by identifying instances that can be stopped or terminated.

## Key Features

- **AWS RDS Integration**: Fetches and processes data from AWS RDS.
- **Cost Savings Recommendations**: Identifies idle RDS instances that can be stopped or terminated to save costs.
- **Performance and Security Insights**: Provides detailed analysis on performance and security metrics.

## Configuration Parameters

### AWS Configuration

- **aws_access_key_id**: AWS access key ID.
- **aws_secret_access_key**: AWS secret access key.
- **aws_region**: AWS region.

### Plugin Specific Configuration

- **cpu_utilization**: CPU utilization threshold for determining idle instances. Default = 5%
- **num_connections**: Number of connections threshold for determining idle instances. Default = 100000

## Example Configuration

```yaml
aws_access_key_id: your_access_key_id
aws_secret_access_key: your_secret_access_key
aws_region: your_aws_region
```