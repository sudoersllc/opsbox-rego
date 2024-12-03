# Unattached EIPs Plugin

## Overview

The Unattached EIPs Plugin identifies Elastic IPs (EIPs) that are not associated with any running instances, helping to reduce costs by releasing unused EIPs.

## Key Features

- **AWS EC2 Integration**: Fetches and processes data from AWS EC2.
- **Cost Savings Recommendations**: Identifies EIPs that can be released to save costs.
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