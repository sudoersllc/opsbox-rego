# Console Access IAM Plugin

## Overview

The Console Access IAM Plugin identifies IAM users with console access enabled, helping to enhance security by ensuring only necessary users have console access.

## Key Features

- **AWS IAM Integration**: Fetches and processes data from AWS IAM.
- **Security Recommendations**: Identifies IAM users with console access to improve security.
- **Detailed Analysis**: Provides detailed information on IAM users with console access.

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