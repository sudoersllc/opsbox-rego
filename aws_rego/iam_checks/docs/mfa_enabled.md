# IAM Users Without MFA Plugin

## Overview

The IAM Users Without MFA Plugin identifies IAM users who do not have Multi-Factor Authentication (MFA) enabled, helping to enhance security by ensuring all users have MFA enabled.

## Key Features

- **AWS IAM Integration**: Fetches and processes data from AWS IAM.
- **Security Recommendations**: Identifies IAM users without MFA to improve security.
- **Detailed Analysis**: Provides detailed information on IAM users without MFA.

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