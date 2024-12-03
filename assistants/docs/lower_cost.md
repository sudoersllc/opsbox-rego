# LowerCost Plugin

## Overview

The LowerCost Plugin analyzes AWS EC2 instances and provides recommendations for cost savings by suggesting lower-cost instance types.

## Key Features

- **AWS EC2 Integration**: Fetches and processes data from AWS EC2.
- **Cost Savings Recommendations**: Identifies opportunities to downgrade instances to save costs using a special calculator.
- **Detailed Analysis**: Provides detailed pricing comparisons and potential savings.

## Configuration Parameters

### LowerCost Configuration

- **aws_access_key_id**: AWS access key ID.
- **aws_secret_access_key**: AWS secret access key.
- **aws_region**: AWS region.

## Example Configuration

```yaml
aws_access_key_id: your_access_key_id
aws_secret_access_key: your_secret_access_key
aws_region: your_aws_region
```