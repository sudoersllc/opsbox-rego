# Slack Output Plugin for Opsbox

## Overview

The SlackOutput Plugin processes and sends results to a specified Slack channel, allowing for easy communication and reporting of findings.

*This output plugin can be used by adding `slack_out` to your pipeline.*

## Features

- **Slack Integration**: Sends results to a Slack channel.

## Configuration Parameters

| Parameter      | Type | Description                                    | Required | Default |
|----------------|------|------------------------------------------------|----------|---------|
| slack_token    | str  | The Slack token to use.                        | Yes      | -       |
| slack_channel  | str  | The Slack channel to send the message to.      | Yes      | -       |