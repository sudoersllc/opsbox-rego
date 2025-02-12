from pluggy import HookimplMarker
from pydantic import BaseModel, Field
from loguru import logger
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from opsbox import Result


from typing import TYPE_CHECKING, Annotated

hookimpl = HookimplMarker("opsbox")

if TYPE_CHECKING:
    pass


class SlackOutput:
    """
    Plugin for sending results to a Slack channel.
    """

    def __init__(self):
        pass

    @hookimpl
    def grab_config(self):
        """
        Return the plugin's configuration
        """

        class SlackConfig(BaseModel):
            """Configuration for the slack output."""
            slack_token: Annotated[str, Field(description="The Slack token to use.")]
            slack_channel: Annotated[str, Field(description="The Slack channel to send the message to.")]

        return SlackConfig

    @hookimpl
    @logger.catch(reraise=True)
    def activate(self):
        """
        Initialize the plugin.
        """
        self.client = WebClient(token=self.model.slack_token)

    @hookimpl
    def set_data(self, model: BaseModel):
        """
        Set the data for the plugin based on the model.
        """
        self.model = model

    @hookimpl
    def proccess_results(self, results: list["Result"]):
        """
        Send the results to Slack.

        Args:
            results (list[FormattedResult]): The formatted results from the checks.
        """

        client = self.client
        channel = self.model.slack_channel
        for result in results:
            try:
                response = client.chat_postMessage(
                    channel=channel, text=result.formatted
                )
                if not response["ok"]:
                    raise ValueError("Slack API response indicates failure.")
            except SlackApiError as e:
                logger.error(f"Error sending message to Slack: {e.response['error']}")
