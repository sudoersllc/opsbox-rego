# Jira Output Plugin for Opsbox

## Overview

The JiraOutput Plugin processes and creates Jira issues based on the results of checks, helping to manage and track cost-saving recommendations and other tasks.

*This output plugin can be used by adding `jira_out` to your pipeline.*

## Features

- **Jira Integration**: Fetches and processes data from Jira.
- **Issue Creation**: Creates detailed Jira issues based on the provided results.

## Configuration Parameters

| Parameter         | Type | Description                                      | Required | Default |
|-------------------|------|--------------------------------------------------|----------|---------|
| JIRA_USERNAME     | str  | The URL of the Jira instance.                    | Yes      | -       |
| JIRA_EMAIL        | str  | The email to authenticate to Jira with.          | Yes      | -       |
| JIRA_API_TOKEN    | str  | The API key to authenticate to Jira with.        | Yes      | -       |
| JIRA_PROJECT_KEY  | str  | The Jira project to create issues in.            | Yes      | -       |

***Requires LLM***
