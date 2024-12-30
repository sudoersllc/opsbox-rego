# opsbox-email-output Plugin

## Overview

The `email_out` plugin processes and creates emails based on the results of checks, allowing for easy communication and reporting of findings.

## Key Features

- **Email Integration**: Sends results via email.
- **Customizable SMTP Settings**: Allows specifying SMTP server details.

## Configuration Parameters

### Email Configuration

- **smtp_username**: The username for the SMTP server.
- **smtp_password**: The password for the SMTP server.
- **smtp_server**: The SMTP server to use.
- **smtp_port**: The port to use for the SMTP server.
- **receiver_email_list**: A comma-separated list of email addresses to send the email to.


## Example Configuration

```yaml
smtp_username: your_smtp_username
smtp_password: your_smtp_password
smtp_server: your_smtp_server
smtp_port: your_smtp_port
receiver_email_list: your_receiver_email_list
```