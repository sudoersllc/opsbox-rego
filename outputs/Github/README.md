# Github Output Plugin for Opsbox

## Overview

The GithubOutput Plugin processes and creates GitHub ticket issues based on the results of checks, helping to manage and track cost-saving recommendations and other tasks.

*This output plugin can be used by adding `github_out` to your pipeline.*

## Features

- **GitHub Integration**: Fetches and processes data from GitHub.
- **Issue Creation**: Creates detailed GitHub issues based on the provided results.
- **Customizable Labels**: Allows setting labels for the created issues.

## Configuration Parameters

| Parameter            | Type    | Description                                           | Required | Default |
|----------------------|---------|-------------------------------------------------------|----------|---------|
| github_token         | str     | The token for the GitHub user.                        | Yes      | -       |
| repo_owner           | str     | The owner of the repository.                          | Yes      | -       |
| repo_name            | str     | The name of the repository.                           | Yes      | -       |
| labels               | str\|None | The labels to apply to the issue.                     | No       | None    |
| create_description   | bool    | Whether to create a description instead of an issue.  | No       | False   |

***Description creation requires LLM***
