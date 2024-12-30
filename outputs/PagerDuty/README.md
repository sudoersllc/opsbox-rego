# opsbox-pagerduty-output Plugin

## Overview

The `pagerduty_out` Plugin processes and sends results to PagerDuty, allowing for incident creation and management based on the findings.

***LLM required for description creation***
## Key Features

- **PagerDuty Integration**: Sends results to PagerDuty.
- **Customizable Incident Creation**: Allows specifying whether to create a description or an issue.

## Configuration Parameters

### PagerDuty Configuration

- **routing_key**: The routing key to use.
- **create_description**: Whether to create a description instead of an issue.

## Example Configuration

```yaml
routing_key: your_routing_key
create_description: true
```