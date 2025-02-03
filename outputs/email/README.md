# Email Output Plugin for Opsbox

## Overview

The EmailOutput Plugin processes and creates emails based on the results of checks, allowing for easy communication and reporting of findings.

*This output plugin can be used by adding `email_out` to your pipeline.*

## Features

- **Email Integration**: Sends results via email.

## Configuration Parameters

| Parameter            | Type | Description                                                                 | Required | Default |
|----------------------|------|-----------------------------------------------------------------------------|----------|---------|
| smtp_username        | str  | The username for the SMTP server.                                           | Yes      | -       |
| smtp_password        | str  | The password for the SMTP server.                                           | Yes      | -       |
| smtp_server          | str  | The SMTP server to use.                                                     | Yes      | -       |
| smtp_port            | str  | The port to use for the SMTP server.                                        | Yes      | -       |
| receiver_email_list  | str  | A comma-separated list of email addresses to send the email to.             | Yes      | -       |