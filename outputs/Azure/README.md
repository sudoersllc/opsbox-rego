# opsbox-azure-output Plugin

## Overview

The `azure_out` Plugin processes and creates Azure DevOps ticket issues based on the results of checks, helping to manage and track cost-saving recommendations and other tasks.

***Description creation requires LLM***

## Key Features

- **Azure DevOps Integration**: Fetches and processes data from Azure DevOps.
- **Issue Creation**: Creates detailed Azure DevOps issues based on the provided results.
- **Customizable Priority and Tags**: Allows setting priority and tags for the created issues.

## Configuration Parameters

### Azure DevOps Configuration

- **azure_devops_token**: The personal access token for Azure DevOps.
- **azure_devops_organization**: The name of the Azure DevOps organization.
- **azure_devops_project**: The name of the Azure DevOps project.
- **azure_devops_username**: The username for Azure DevOps.
- **azure_devops_priority**: The priority of the work item (default: 4).
- **tags**: The tags to apply to the work item (optional).
- **create_description**: Whether to create a description instead of an issue (default: false).


## Example Configuration

```yaml
azure_devops_token: your_azure_devops_token
azure_devops_organization: your_azure_devops_organization
azure_devops_project: your_azure_devops_project
azure_devops_username: your_azure_devops_username
azure_devops_priority: 4
tags: your_tags
create_description: false
```