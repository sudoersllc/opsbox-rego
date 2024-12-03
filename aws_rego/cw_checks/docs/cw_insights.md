# CW Insights Plugin

## Overview

The CW Insights Plugin analyzes AWS CloudWatch metrics to provide insights into cost savings, performance, and security optimizations. It leverages OpenAI models to process and interpret the data, offering actionable recommendations based on the metrics collected.

***Requires LLM***

## Key Features

- **AWS CloudWatch Integration**: Fetches and processes metrics from AWS CloudWatch.
- **OpenAI Integration**: Uses OpenAI models for data analysis and generating insights.
- **Cost Savings Recommendations**: Identifies metrics that can help in reducing costs.
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
oai_key: your_openai_api_key
```