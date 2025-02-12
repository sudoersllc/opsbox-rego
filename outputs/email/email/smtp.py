from pluggy import HookimplMarker
from pydantic import BaseModel, Field
from loguru import logger
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Annotated
from opsbox import Result

hookimpl = HookimplMarker("opsbox")


class EmailOutput:
    """Plugin for outputting results to an email address."""

    def __init__(self):
        pass

    @hookimpl
    def grab_config(self):
        """Return the plugin's configuration."""

        class EmailConfig(BaseModel):
            """Configuration for the email output."""

            smtp_username: Annotated[str, Field(description="The username for the SMTP server.")]
            smtp_password: Annotated[str, Field(description="The password for the SMTP server.")]
            smtp_server: Annotated[str, Field(description="The SMTP server to use.")]
            smtp_port: Annotated[int, Field(description="The port to use for the SMTP server.")]
            receiver_email_list: Annotated[
                str, Field(description="A comma-separated list of email addresses to send the email to.")
            ]

        return EmailConfig

    @hookimpl
    def set_data(self, model: BaseModel):
        """Set the data for the plugin based on the model."""
        self.model = model

    @hookimpl
    def proccess_results(self, results: list["Result"]):
        """
        Emails the check results to the specified email addresses.

        Args:
            results (list[Result]): The formatted results from the checks.
        """

        logger.info("Sending email with check results")
        msg = MIMEMultipart()
        logger.info(
            f"Sending email from {self.model.smtp_username} to {self.model.receiver_email_list}"
        )
        msg["From"] = self.model.smtp_username
        msg["To"] = self.model.receiver_email_list
        try:
            for result in results:
                body = result.formatted
                msg.attach(MIMEText(body, "plain"))
                msg["Subject"] = f"OpsBox Check Results: {result.result_name}"
                server = smtplib.SMTP(self.model.smtp_server, self.model.smtp_port)
                logger.info("Starting TLS...")
                server.starttls()
                logger.info(
                    f"Logging in to {self.model.smtp_server} on port {self.model.smtp_port}"
                )
                server.login(self.model.smtp_username, self.model.smtp_password)
                logger.info("Sending email...")
                text = msg.as_string()
                server.sendmail(
                    self.model.smtp_username,
                    self.model.receiver_email_list.split(","),
                    text,
                )
                server.quit()
                logger.success("Email sent successfully!")
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            logger.error(f"Error on line {e.__traceback__.tb_lineno}")

            return
        logger.success("Results sent via email!")
