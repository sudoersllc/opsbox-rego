import requests
from pydantic import BaseModel
from loguru import logger

from .azure.azure import AzureOutput, AppConfig  # type: ignore
from llama_index.core import VectorStoreIndex
from llama_index.core.program import LLMTextCompletionProgram


def test_grab_config():
    """
    Ensure that grab_config returns a valid Pydantic model class with expected fields.
    """
    azure = AzureOutput()
    ConfigCls = azure.grab_config()
    # Check that the returned config is a subclass of BaseModel
    assert issubclass(ConfigCls, BaseModel)
    # Instantiate the config with the required fields
    config_instance = ConfigCls(
        azure_devops_token="dummy_token",
        azure_devops_organization="dummy_org",
        azure_devops_project="dummy_project",
        azure_devops_username="dummy_user",
    )
    # Verify that a field was set correctly.
    assert config_instance.azure_devops_token == "dummy_token"


def test_set_data():
    """
    Verify that set_data stores the model and credentials properly.
    """
    azure = AzureOutput()
    ConfigCls = azure.grab_config()
    config_instance = ConfigCls(
        azure_devops_token="token",
        azure_devops_organization="org",
        azure_devops_project="project",
        azure_devops_username="user",
        azure_devops_priority=2,
        tags="my_tag",
        create_description=False,
    )
    azure.set_data(config_instance)
    assert azure.model == config_instance
    assert azure.credentials == config_instance.model_dump()


def test_proccess_results_success(tmp_path, monkeypatch):
    """
    Test the normal flow where:
      - A result file is written,
      - Attachment upload and work item creation succeed,
      - create_description flag is False (so no extra description processing).
    """
    azure = AzureOutput()
    ConfigCls = azure.grab_config()
    config_instance = ConfigCls(
        azure_devops_token="token",
        azure_devops_organization="org",
        azure_devops_project="project",
        azure_devops_username="user",
        azure_devops_priority=2,
        tags="my_tag",
        create_description=False,
    )
    azure.set_data(config_instance)

    # Create a dummy check result.
    result = {
        "check_name": "test_check",
        "formatted": "This is a test formatted result.",
    }

    # Change working directory to a temporary path so files are created there.
    monkeypatch.chdir(tmp_path)

    # Create a dummy response class for simulating requests.post responses.
    class DummyResponse:
        def __init__(self, status_code, json_data):
            self.status_code = status_code
            self._json = json_data
            self.text = "dummy response text"

        def json(self):
            return self._json

    # Define a fake requests.post function.
    def fake_requests_post(url, headers, json=None, data=None, timeout=15):
        if "attachments" in url:
            # Simulate a successful attachment upload.
            return DummyResponse(200, {"url": "http://dummy.attachment.url"})
        elif "workitems" in url:
            # Simulate a successful work item creation.
            return DummyResponse(200, {"url": "http://dummy.workitem.url"})
        return DummyResponse(404, {})

    monkeypatch.setattr(requests, "post", fake_requests_post)

    # Invoke the method under test.
    azure.proccess_results([result])

    # Verify that the file was created and its content is correct.
    file_path = tmp_path / "test_check.txt"
    assert file_path.exists()
    file_content = file_path.read_text()
    assert file_content == "This is a test formatted result."


def test_proccess_results_attachment_failure(tmp_path, monkeypatch, capsys):
    """
    Simulate a failure during the attachment upload call (i.e. non-200 status code)
    and verify that a failure message is printed.
    """
    azure = AzureOutput()
    ConfigCls = azure.grab_config()
    config_instance = ConfigCls(
        azure_devops_token="token",
        azure_devops_organization="org",
        azure_devops_project="project",
        azure_devops_username="user",
        azure_devops_priority=2,
        tags="my_tag",
        create_description=False,
    )
    azure.set_data(config_instance)

    result = {"check_name": "fail_check", "formatted": "Failure test result."}

    monkeypatch.chdir(tmp_path)

    class DummyResponse:
        def __init__(self, status_code, json_data=None):
            self.status_code = status_code
            self._json = json_data or {}
            self.text = "error response"

        def json(self):
            return self._json

    def fake_requests_post(url, headers, json=None, data=None, timeout=15):
        if "attachments" in url:
            # Simulate a failure (e.g. status 400) for the attachment upload.
            return DummyResponse(400, {"error": "Upload failed"})
        elif "workitems" in url:
            return DummyResponse(200, {"url": "http://dummy.workitem.url"})
        return DummyResponse(404, {})

    monkeypatch.setattr(requests, "post", fake_requests_post)

    # Call proccess_results.
    azure.proccess_results([result])

    # Capture printed output and verify that a failure message was printed.
    captured = capsys.readouterr().out
    assert "Failed to upload file" in captured


def test_proccess_results_exception(tmp_path, monkeypatch):
    """
    Simulate an exception (e.g. from requests.post) and ensure that
    proccess_results catches it and logs an error.
    """
    azure = AzureOutput()
    ConfigCls = azure.grab_config()
    config_instance = ConfigCls(
        azure_devops_token="token",
        azure_devops_organization="org",
        azure_devops_project="project",
        azure_devops_username="user",
        azure_devops_priority=2,
        tags="my_tag",
        create_description=False,
    )
    azure.set_data(config_instance)

    result = {"check_name": "exception_check", "formatted": "Exception test result."}

    monkeypatch.chdir(tmp_path)

    # Force requests.post to always raise an exception.
    def fake_requests_post(url, headers, json=None, data=None, timeout=15):
        raise Exception("Simulated exception")

    monkeypatch.setattr(requests, "post", fake_requests_post)

    # Optionally, capture logger.error calls by monkeypatching logger.error.
    error_messages = []

    def fake_logger_error(msg, *args, **kwargs):
        error_messages.append(msg)

    monkeypatch.setattr(logger, "error", fake_logger_error)

    # Run the method; it should not raise an exception (it is caught internally).
    azure.proccess_results([result])

    # Verify that an error was logged.
    assert any("Error sending Ticket" in msg for msg in error_messages)
    # The file write happens before the failing network call.
    file_path = tmp_path / "exception_check.txt"
    assert file_path.exists()


def test_proccess_results_create_description_none(tmp_path, monkeypatch):
    """
    Test the branch where create_description is True and AppConfig.embed_model is None.
    In that case, LLMTextCompletionProgram.from_defaults is invoked.
    """
    azure = AzureOutput()
    ConfigCls = azure.grab_config()
    config_instance = ConfigCls(
        azure_devops_token="token",
        azure_devops_organization="org",
        azure_devops_project="project",
        azure_devops_username="user",
        azure_devops_priority=2,
        tags="my_tag",
        create_description=True,  # Trigger description creation
    )
    azure.set_data(config_instance)

    result = {"check_name": "desc_none", "formatted": "Description test result."}

    monkeypatch.chdir(tmp_path)

    # Monkeypatch LLMTextCompletionProgram.from_defaults to avoid external calls.
    def fake_from_defaults(*args, **kwargs):
        class DummyProgram:
            def __call__(self, document):
                # In the real code, the program would generate a description.
                # Here, we do nothing.
                return "dummy response"

        return DummyProgram()

    monkeypatch.setattr(LLMTextCompletionProgram, "from_defaults", fake_from_defaults)

    # Monkeypatch requests.post (for attachment and work item creation).
    class DummyResponse:
        def __init__(self, status_code, json_data):
            self.status_code = status_code
            self._json = json_data
            self.text = "dummy response text"

        def json(self):
            return self._json

    def fake_requests_post(url, headers, json=None, data=None, timeout=15):
        if "attachments" in url:
            return DummyResponse(200, {"url": "http://dummy.attachment.url"})
        elif "workitems" in url:
            return DummyResponse(200, {"url": "http://dummy.workitem.url"})
        return DummyResponse(404, {})

    monkeypatch.setattr(requests, "post", fake_requests_post)

    conf = AppConfig()
    conf.embed_model = None
    conf.llm = "None"

    azure.proccess_results([result])

    # Check that the result file was written.
    file_path = tmp_path / "desc_none.txt"
    assert file_path.exists()
    content = file_path.read_text()
    assert content == "Description test result."


def test_proccess_results_create_description_with_embed(tmp_path, monkeypatch):
    """
    Test the branch where create_description is True and an embed_model is provided.
    In this branch the code uses VectorStoreIndex and a query engine.
    """
    azure = AzureOutput()
    ConfigCls = azure.grab_config()
    config_instance = ConfigCls(
        azure_devops_token="token",
        azure_devops_organization="org",
        azure_devops_project="project",
        azure_devops_username="user",
        azure_devops_priority=2,
        tags="my_tag",
        create_description=True,  # Trigger description creation
    )
    azure.set_data(config_instance)

    result = {"check_name": "desc_embed", "formatted": "Embed test result."}

    monkeypatch.chdir(tmp_path)

    conf = AppConfig()
    conf.embed_model = "dummy_model"
    conf.llm = "None"

    # Monkeypatch VectorStoreIndex.from_documents to return a dummy index.
    class DummyIndex:
        def as_query_engine(self, llm):
            class DummyQueryEngine:
                def query(self, query_text):
                    # Simulate a generated description.
                    return "Detailed description generated"

            return DummyQueryEngine()

    monkeypatch.setattr(
        VectorStoreIndex, "from_documents", lambda docs, embed_model: DummyIndex()
    )

    # Monkeypatch requests.post as in other tests.
    class DummyResponse:
        def __init__(self, status_code, json_data):
            self.status_code = status_code
            self._json = json_data
            self.text = "dummy response text"

        def json(self):
            return self._json

    def fake_requests_post(url, headers, json=None, data=None, timeout=15):
        if "attachments" in url:
            return DummyResponse(200, {"url": "http://dummy.attachment.url"})
        elif "workitems" in url:
            return DummyResponse(200, {"url": "http://dummy.workitem.url"})
        return DummyResponse(404, {})

    monkeypatch.setattr(requests, "post", fake_requests_post)

    azure.proccess_results([result])

    # Verify that the file is created.
    file_path = tmp_path / "desc_embed.txt"
    assert file_path.exists()
    content = file_path.read_text()
    # The file content is always the original result["formatted"].
    assert content == "Embed test result."
