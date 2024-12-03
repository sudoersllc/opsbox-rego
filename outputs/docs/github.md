# GithubOutput Plugin

## Overview

The GithubOutput Plugin processes and creates GitHub ticket issues based on the results of checks, helping to manage and track cost-saving recommendations and other tasks.

***Description creation requires LLM***

## Key Features

- **GitHub Integration**: Fetches and processes data from GitHub.
- **Issue Creation**: Creates detailed GitHub issues based on the provided results.
- **Customizable Labels**: Allows setting labels for the created issues.

## Configuration Parameters

### GitHub Configuration

- **github_token**: The token for the GitHub user.
- **repo_owner**: The owner of the repository.
- **repo_name**: The name of the repository.
- **labels**: The labels to apply to the issue (optional).
- **create_description**: Whether to create a description instead of an issue (default: false).


## Example Configuration

```yaml
github_token: your_github_token
repo_owner: your_repo_owner
repo_name: your_repo_name
labels: your_labels
create_description: false
```