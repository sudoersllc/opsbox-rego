import pytest
import os
import tempfile
import shutil
from unittest.mock import patch
from pydantic import BaseModel
from opsbox import Result
from .json_file.json_file import JSONFileOutput  # type: ignore
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
def json_plugin():
    return JSONFileOutput()


def test_grab_config(json_plugin):
    conf_cls = json_plugin.grab_config()
    conf = conf_cls()
    assert conf.output_folder == "./findings/"


def test_activate_creates_folder(json_plugin):
    temp_dir = tempfile.mkdtemp()
    try:

        class MockModel(BaseModel):
            output_folder: str = temp_dir

        json_plugin.set_data(MockModel())
        json_plugin.activate()
        assert os.path.exists(temp_dir)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_set_data(json_plugin):
    class MockModel(BaseModel):
        output_folder: str = "fake_folder"

    model = MockModel()
    json_plugin.set_data(model)
    assert json_plugin.model == model


def test_proccess_results_success(json_plugin):
    temp_dir = tempfile.mkdtemp()
    try:

        class MockModel(BaseModel):
            output_folder: str = temp_dir

        json_plugin.set_data(MockModel())
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
        json_plugin.proccess_results(results)
        for r in results:
            file_path = os.path.join(temp_dir, r.relates_to, f"{r.result_name}.json")
            assert os.path.exists(file_path)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_proccess_results_typeerror(json_plugin, loguru_caplog):
    temp_dir = tempfile.mkdtemp()
    try:

        class MockModel(BaseModel):
            output_folder: str = temp_dir

        json_plugin.set_data(MockModel())
        bad_result = Result(
            relates_to="bad",
            result_name="bad",
            result_description="bad desc",
            details={"set_data": {1, 2}},
            formatted="some text",
        )
        json_plugin.proccess_results([bad_result])
        assert "Failed to serialize" in loguru_caplog.text
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@patch("builtins.open", side_effect=IOError("mocked IO error"))
def test_proccess_results_ioerror(mock_open, json_plugin, loguru_caplog):
    temp_dir = tempfile.mkdtemp()
    try:

        class MockModel(BaseModel):
            output_folder: str = temp_dir

        json_plugin.set_data(MockModel())
        good_result = Result(
            relates_to="io_error",
            result_name="res",
            result_description="desc",
            details={"ok": True},
            formatted="stuff",
        )
        json_plugin.proccess_results([good_result])
        assert "IO error while writing" in loguru_caplog.text
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
