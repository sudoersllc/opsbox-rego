# Overdue API Keys Plugin

## Overview

The Overdue API Keys Plugin identifies IAM API keys that are overdue, helping to enhance security by ensuring all API keys are rotated regularly.

## Key Features

- **AWS IAM Integration**: Fetches and processes data from AWS IAM.
- **Security Recommendations**: Identifies overdue API keys to improve security.
- **Detailed Analysis**: Provides detailed information on overdue API keys.

## Configuration Parameters

### AWS Configuration

- **aws_access_key_id**: AWS access key ID.
- **aws_secret_access_key**: AWS secret access key.
- **aws_region**: AWS region.

### Plugin Specific Configuration

- **rotation_threshold_days**: The threshold for API key rotation (in days). Default: 90.

## Example Configuration

```yaml
aws_access_key_id: your_access_key_id
aws_secret_access_key: your_secret_access_key
aws_region: your_aws_region
```