# opsbox-jira-output Plugin

## Overview

The `jira_out` Plugin processes and creates Jira issues based on the results of checks, helping to manage and track cost-saving recommendations and other tasks.

***Requires LLM***

## Key Features

- **Jira Integration**: Fetches and processes data from Jira.
- **Issue Creation**: Creates detailed Jira issues based on the provided results.
- **Customizable Project Key**: Allows specifying the Jira project to create issues in.

## Configuration Parameters

### Jira Configuration

- **jira_url**: The URL of the Jira instance.
- **jira_email**: The email to authenticate to Jira with.
- **jira_api_token**: The API key to authenticate to Jira with.
- **jira_project_key**: The Jira project to create issues in.


## Example Configuration

```yaml
jira_url: your_jira_url
jira_email: your_jira_email
jira_api_token: your_jira_api_token
jira_project_key: your_jira_project_key
```