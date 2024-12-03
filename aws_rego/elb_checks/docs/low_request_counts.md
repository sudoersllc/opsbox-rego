
# Low Request Count Load Balancers

## Overview

The Low Request Count Load Balancers check identifies load balancers with low request counts.

## Key Features

- **AWS ELB Integration**: Fetches and processes data from AWS ELB.
- **Request Count Analysis**: Identifies load balancers with low request counts.
- **Performance Insights**: Provides detailed analysis on performance metrics.

## Configuration Parameters

### AWS Configuration

- **aws_access_key_id**: AWS access key ID.
- **aws_secret_access_key**: AWS secret access key.
- **aws_region**: AWS region.

### Check Configuration

- **period**: 300 (seconds)
- **request_threshold**: 100 (requests)

## Example Configuration

```yaml
aws_access_key_id: your_access_key_id
aws_secret_access_key: your_secret_access_key
aws_region: your_aws_region
```