import pytest
import os
import tempfile
import shutil
from pydantic import BaseModel
from opsbox import Result
from .text_file.text_file import TextFileOutput  # type: ignore
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
def text_plugin():
    return TextFileOutput()


def test_grab_config(text_plugin):
    conf_cls = text_plugin.grab_config()
    conf = conf_cls()
    assert conf.output_folder == "./findings/"


def test_activate_creates_folder(text_plugin):
    temp_dir = tempfile.mkdtemp()
    try:

        class MockModel(BaseModel):
            output_folder: str = temp_dir

        text_plugin.set_data(MockModel())
        text_plugin.activate()
        assert os.path.exists(temp_dir)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_set_data(text_plugin):
    class MockModel(BaseModel):
        output_folder: str = "fake_folder"

    model = MockModel()
    text_plugin.set_data(model)
    assert text_plugin.model == model


def test_proccess_results_success(text_plugin):
    temp_dir = tempfile.mkdtemp()
    try:

        class MockModel(BaseModel):
            output_folder: str = temp_dir

        text_plugin.set_data(MockModel())
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
        text_plugin.proccess_results(results)
        for r in results:
            file_path = os.path.join(temp_dir, r.relates_to, f"{r.result_name}.txt")
            assert os.path.exists(file_path)
            # assert contents of the file
            with open(file_path, "r", encoding="utf-8") as f:
                contents = f.read()
                assert contents == r.formatted
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
