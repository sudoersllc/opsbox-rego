# High Error Rate Load Balancers

## Overview

The High Error Rate Load Balancers check identifies load balancers with a high error rate.

## Key Features

- **AWS ELB Integration**: Fetches and processes data from AWS ELB.
- **Error Rate Analysis**: Identifies load balancers with high error rates.
- **Performance Insights**: Provides detailed analysis on performance metrics.

## Configuration Parameters

### AWS Configuration

- **aws_access_key_id**: AWS access key ID.
- **aws_secret_access_key**: AWS secret access key.
- **aws_region**: AWS region.

### Check Configuration

- **period**: 300 (seconds)
- **threshold**: 5 (error rate percentage)

## Example Configuration

```yaml
aws_access_key_id: your_access_key_id
aws_secret_access_key: your_secret_access_key
aws_region: your_aws_region
```