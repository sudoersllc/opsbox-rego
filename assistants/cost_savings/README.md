# opsbox-cost-savings Plugin

## Overview

The `cost_savings` plugin analyzes data to provide detailed recommendations for cost savings, ensuring no data point is left unchecked.

**LLM configuration required**

## Key Features

- **Comprehensive Data Analysis**: Reviews all types of data to uncover cost-saving opportunities.
- **Detailed Recommendations**: Provides step-by-step breakdowns of potential savings.
- **LLM Integration**: Utilizes LLM for generating detailed recommendations if enabled.

## Configuration Parameters

### Cost Savings Configuration

- **arrigator**: Whether to aggregate the data and generate one response.
- **discard_prior**: Whether to discard the data before and leave only cost-saving data.

## Example Configuration

```yaml
arrigator: true
discard_prior: false
```