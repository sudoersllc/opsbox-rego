# Stray Instances Plugin

## Overview

The Stray Instances Plugin identifies EC2 instances that are not associated with any specific workload or application, helping to reduce costs by terminating unused instances.

## Key Features

- **AWS EC2 Integration**: Fetches and processes data from AWS EC2.
- **Cost Savings Recommendations**: Identifies instances that can be terminated to save costs.
- **Performance and Security Insights**: Provides detailed analysis on performance and security metrics.

## Configuration Parameters

### AWS Configuration

- **aws_access_key_id**: AWS access key ID.
- **aws_secret_access_key**: AWS secret access key.
- **aws_region**: AWS region.

## Default Settings

- **Period**: 300 seconds (5 minutes)
- **Stat**: Average
- **ScanBy**: TimestampDescending

## Example Configuration

```yaml
aws_access_key_id: your_access_key_id
aws_secret_access_key: your_secret_access_key
aws_region: your_aws_region
```