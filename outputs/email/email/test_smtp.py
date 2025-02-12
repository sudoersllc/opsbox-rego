import pytest
from unittest.mock import patch
from pydantic import BaseModel
from opsbox import Result
from .smtp import EmailOutput

import logging
from loguru import logger


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


@pytest.fixture
def email_plugin():
    return EmailOutput()


def test_grab_config(email_plugin):
    conf_cls = email_plugin.grab_config()
    conf = conf_cls(
        smtp_username="user@example.com",
        smtp_password="password",
        smtp_server="smtp.example.com",
        smtp_port=587,
        receiver_email_list="receiver@example.com",
    )
    assert conf.smtp_username == "user@example.com"
    assert conf.smtp_password == "password"
    assert conf.smtp_server == "smtp.example.com"
    assert conf.smtp_port == 587
    assert conf.receiver_email_list == "receiver@example.com"


def test_set_data(email_plugin):
    class MockModel(BaseModel):
        smtp_username: str = "user@example.com"
        smtp_password: str = "password"
        smtp_server: str = "smtp.example.com"
        smtp_port: int = 587
        receiver_email_list: str = "receiver@example.com"

    model = MockModel()
    email_plugin.set_data(model)
    assert email_plugin.model == model


@patch("smtplib.SMTP")
def test_proccess_results_success(mock_smtp, email_plugin):
    class MockModel(BaseModel):
        smtp_username: str = "user@example.com"
        smtp_password: str = "password"
        smtp_server: str = "smtp.example.com"
        smtp_port: int = 587
        receiver_email_list: str = "receiver@example.com"

    email_plugin.set_data(MockModel())
    results = [
        Result(
            relates_to="case1",
            result_name="res1",
            result_description="description1",
            details={"foo": "bar"},
            formatted="some formatted text",
        ),
        Result(
            relates_to="case2",
            result_name="res2",
            result_description="description2",
            details={"baz": 123},
            formatted="other formatted text",
        ),
    ]

    email_plugin.proccess_results(results)

    mock_smtp_instance = mock_smtp.return_value
    assert mock_smtp_instance.starttls.called
    assert mock_smtp_instance.sendmail.called
    assert mock_smtp_instance.login.called
    assert mock_smtp_instance.quit.called


@patch("smtplib.SMTP.starttls", side_effect=Exception("Test Exception"))
def test_proccess_results_exception(mock_starttls, email_plugin, loguru_caplog):
    class MockModel(BaseModel):
        smtp_username: str = "user@example.com"
        smtp_password: str = "password"
        smtp_server: str = "smtp.example.com"
        smtp_port: int = 587
        receiver_email_list: str = "receiver@example.com"

    email_plugin.set_data(MockModel())
    results = [
        Result(
            relates_to="case1",
            result_name="res1",
            result_description="description1",
            details={"foo": "bar"},
            formatted="some formatted text",
        ),
        Result(
            relates_to="case2",
            result_name="res2",
            result_description="description2",
            details={"baz": 123},
            formatted="other formatted text",
        ),
    ]

    email_plugin.proccess_results(results)
    assert "Error sending email" in loguru_caplog.text
