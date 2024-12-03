# Scaling Down RDS Instances

## Overview

Scaling down RDS instances involves reducing the allocated resources (such as CPU, memory, or storage) to better match the current workload. This can help optimize costs and improve resource utilization.

## Key Features

- **Resource Optimization**: Adjusts the instance size to better fit the workload.
- **Cost Savings**: Reduces costs by allocating fewer resources.
- **Performance Monitoring**: Continuously monitors performance to ensure the instance is appropriately sized.

## Configuration Parameters

### AWS Configuration

- **aws_access_key_id**: AWS access key ID.
- **aws_secret_access_key**: AWS secret access key.
- **aws_region**: AWS region.

### Plugin Specific Configuration

- **utilization_threshold**: The CPU utilization threshold (in percentage) below which an RDS instance is considered underutilized. Default: `20`.

## Example Configuration

```yaml
aws_access_key_id: your_access_key_id
aws_secret_access_key: your_secret_access_key
aws_region: your_aws_region
```