import pytest
from unittest.mock import patch, MagicMock
from pydantic import BaseModel
from slack_sdk.errors import SlackApiError
from loguru import logger
from opsbox import Result
from .slack.slack import SlackOutput # type: ignore
import logging


@pytest.fixture
def slack_plugin():
    return SlackOutput()


slack_mock_data = {
    "ok": True,
    "channel": "C1234567890",
    "ts": "1405894322.002768",
    "message": {
        "text": "Here's a message for you",
        "username": "bot",
        "bot_id": "B12345678",
        "attachments": [
            {
                "fallback": "Required plain-text summary of the attachment.",
                "color": "#36a64f",
                "pretext": "Optional text that appears above the attachment block",
                "author_name": "Bobby Tables",
                "author_link": "http://flickr.com/bobby/",
                "author_icon": "http://flickr.com/icons/bobby.jpg",
                "title": "Slack API Documentation",
                "title_link": "https://api.slack.com/",
                "text": "Optional text that appears within the attachment",
                "fields": [{"title": "Priority", "value": "High", "short": False}],
                "image_url": "http://my-website.com/path/to/image.jpg",
                "thumb_url": "http://example.com/path/to/thumb.png",
                "footer": "Slack API",
                "footer_icon": "https://platform.slack-edge.com/img/default_application_icon.png",
                "ts": 123456789,
            }
        ],
    },
}


@pytest.fixture
def loguru_caplog(caplog):
    class PropagateHandler(logging.Handler):
        def emit(self, record):
            logging.getLogger(record.name).handle(record)

    # Remove default Loguru handlers
    logger.remove()

    # Add handler to propagate Loguru logs to standard logging
    logger.add(PropagateHandler(), level="DEBUG")

    yield caplog  # Provide normal caplog usage

    # Clean up
    logger.remove()


def test_grab_config(slack_plugin):
    conf_cls = slack_plugin.grab_config()
    conf = conf_cls(slack_token="fake_token", slack_channel="fake_channel")
    assert conf.slack_token == "fake_token"
    assert conf.slack_channel == "fake_channel"


def test_activate(slack_plugin):
    class MockModel(BaseModel):
        slack_token: str = "fake_token"
        slack_channel: str = "fake_channel"

    slack_plugin.set_data(MockModel())
    slack_plugin.activate()
    assert slack_plugin.client.token == "fake_token"


def test_set_data(slack_plugin):
    class MockModel(BaseModel):
        slack_token: str = "fake_token"
        slack_channel: str = "fake_channel"

    model = MockModel()
    slack_plugin.set_data(model)
    assert slack_plugin.model == model


@patch("slack_sdk.WebClient.chat_postMessage", return_value=slack_mock_data)
def test_proccess_results_success(mock_post, slack_plugin):
    class MockModel(BaseModel):
        slack_token: str = "fake_token"
        slack_channel: str = "fake_channel"

    slack_plugin.set_data(MockModel())
    slack_plugin.activate()
    results = [
        Result(
            relates_to="case1",
            result_name="res1",
            result_description="description1",
            details={"foo": "bar"},
            formatted="some formatted text",
        )
    ]
    slack_plugin.proccess_results(results)
    mock_post.assert_called_once_with(
        channel="fake_channel", text="some formatted text"
    )


@patch(
    "slack_sdk.WebClient.chat_postMessage",
    side_effect=SlackApiError(message="error", response=MagicMock()),
)
def test_proccess_results_slackapierror(mock_post, slack_plugin, loguru_caplog):
    class MockModel(BaseModel):
        slack_token: str = "fake_token"
        slack_channel: str = "fake_channel"

    slack_plugin.set_data(MockModel())
    slack_plugin.activate()
    bad_result = Result(
        relates_to="case1",
        result_name="res1",
        result_description="description1",
        details={"foo": "bar"},
        formatted="some formatted text",
    )
    with loguru_caplog.at_level("ERROR"):
        slack_plugin.proccess_results([bad_result])
    assert "Error sending message to Slack" in loguru_caplog.text
