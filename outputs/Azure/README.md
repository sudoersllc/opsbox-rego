# Azure Output Plugin for Opsbox

## Overview

The AzureOutput Plugin processes and creates Azure DevOps ticket issues based on the results of checks, helping to manage and track cost-saving recommendations and other tasks.

*This output plugin can be used by adding `azure_out` to your pipeline.*

## Features

- **Azure DevOps Integration**: Fetches and processes data from Azure DevOps.
- **Issue Creation**: Creates detailed Azure DevOps issues based on the provided results.
- **Customizable Priority and Tags**: Allows setting priority and tags for the created issues.

## Configuration Parameters

| Parameter                  | Type    | Description                                           | Required | Default |
|----------------------------|---------|-------------------------------------------------------|----------|---------|
| azure_devops_token         | str     | The personal access token for Azure DevOps.           | Yes      | -       |
| azure_devops_organization  | str     | The name of the Azure DevOps organization.            | Yes      | -       |
| azure_devops_project       | str     | The name of the Azure DevOps project.                 | Yes      | -       |
| azure_devops_username      | str     | The username for Azure DevOps.                        | Yes      | -       |
| azure_devops_priority      | int     | The priority of the work item.                        | No       | 4       |
| tags                       | str\|None | The tags to apply to the work item.                   | No       | None    |
| create_description         | bool    | Whether to create a description instead of an issue.  | No       | False   |

***Description creation requires LLM configuration***