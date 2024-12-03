# Object Last Modified Plugin

## Overview

The Object Last Modified Plugin identifies S3 objects that have not been modified for a specified period, helping to optimize storage costs by identifying objects that can be deleted or archived.

## Key Features

- **AWS S3 Integration**: Fetches and processes data from AWS S3.
- **Cost Savings Recommendations**: Identifies objects that can be deleted or archived to save costs.
- **Performance and Security Insights**: Provides detailed analysis on performance and security metrics.

## Configuration Parameters

### AWS Configuration

- **aws_access_key_id**: AWS access key ID.
- **aws_secret_access_key**: AWS secret access key.
- **aws_region**: AWS region.

### Plugin Specific Configuration

- **modified_period**: The period of inactivity (in days) to consider an object as not modified. Default: `90`.
- **percent_standard**: The threshold for how many items can be in standard storage class when considered unmodified

## Example Configuration

```yaml
aws_access_key_id: your_access_key_id
aws_secret_access_key: your_secret_access_key
aws_region: your_aws_region
```