import base64
import json
import pytest
import requests
from pydantic import BaseModel
from opsbox import AppConfig, Result

from .jira.jira import JiraOutput, SolutionsPlan # type: ignore


class DummyConfig(BaseModel):
    JIRA_USERNAME: str = "dummy_user"
    JIRA_EMAIL: str = "dummy@example.com"
    JIRA_API_TOKEN: str = "dummy_token"
    JIRA_PROJECT_KEY: str = "DUMMY"
    # Note: our code expects a jira_url attribute
    jira_url: str = "http://dummy.jira"

# A simple dummy response to simulate requests responses.
class DummyResponse:
    def __init__(self, status_code, json_data=None, text=""):
        self.status_code = status_code
        self._json = json_data or {}
        self.text = text

    def json(self):
        return self._json

# Fixture to create and initialize a JiraOutput instance with dummy configuration.
@pytest.fixture
def jira_instance():
    instance = JiraOutput()
    dummy_conf = DummyConfig()
    instance.set_data(dummy_conf)
    return instance

# A helper dummy_get to simulate GET requests.
def dummy_get(url, headers, timeout):
    return DummyResponse(200, json_data={"values": [{"id": "epic_field_123"}]})

def test_grab_config():
    """
    Test that grab_config returns a valid Pydantic model class with the required fields.
    :contentReference[oaicite:2]{index=2}
    """
    jira_output = JiraOutput()
    ConfigModel = jira_output.grab_config()
    # Ensure the returned config model is a subclass of BaseModel.
    assert issubclass(ConfigModel, BaseModel)
    # Instantiate it with dummy data.
    instance = ConfigModel(
        JIRA_USERNAME="dummy",
        JIRA_EMAIL="dummy@example.com",
        JIRA_API_TOKEN="dummy_token",
        JIRA_PROJECT_KEY="DUMMY",
    )
    assert instance.JIRA_EMAIL == "dummy@example.com"

def test_set_data(jira_instance):
    """
    Test that set_data correctly sets the plugin’s configuration.
    """
    assert jira_instance.model.JIRA_EMAIL == "dummy@example.com"

def test_activate(jira_instance, monkeypatch):
    """
    Test that activate constructs the proper authentication header and fetches the epic link field id.
    """
    # Monkeypatch requests.get to simulate a valid JSON response.
    monkeypatch.setattr(requests, "get", dummy_get)

    # Compute the expected base64 credentials.
    creds = f"{jira_instance.model.JIRA_EMAIL}:{jira_instance.model.JIRA_API_TOKEN}".encode("utf-8")
    expected_b64 = base64.b64encode(creds).decode("utf-8")

    jira_instance.activate()
    assert jira_instance.auth_headers["Authorization"] == f"Basic {expected_b64}"
    assert jira_instance.auth_headers["Content-Type"] == "application/json"
    assert jira_instance.epic_link_field_id == "epic_field_123"

def test_create_epic_success(jira_instance, monkeypatch):
    """
    Test that _create_epic returns the epic id when the POST is successful.
    """
    def dummy_post(url, headers, data, timeout):
        return DummyResponse(201, json_data={"id": "EPIC123"})
    monkeypatch.setattr(requests, "post", dummy_post)
    monkeypatch.setattr(requests, "get", dummy_get)
    jira_instance.activate()
    epic_id = jira_instance._create_epic("Epic Summary", "Epic Description", "EpicName")
    assert epic_id == "EPIC123"

def test_create_epic_failure(jira_instance, monkeypatch):
    """
    Test that _create_epic raises HTTPError when the POST fails.
    """
    def dummy_post(url, headers, data, timeout):
        return DummyResponse(400, json_data={"error": "Bad Request"}, text="Bad Request")
    monkeypatch.setattr(requests, "post", dummy_post)
    monkeypatch.setattr(requests, "get", dummy_get)
    jira_instance.activate()
    with pytest.raises(requests.HTTPError):
        jira_instance._create_epic("Epic Summary", "Epic Description", "EpicName")

def test_create_task_success(jira_instance, monkeypatch):
    """
    Test that _create_task calls _append_details_to_task when task creation is successful.
    """
    # Record if _append_details_to_task is called.
    called = False
    def dummy_append(issue_key, details):
        nonlocal called
        called = True
    monkeypatch.setattr(jira_instance, "_append_details_to_task", dummy_append)
    def dummy_post(url, headers, data, timeout):
        return DummyResponse(201, json_data={"key": "TASK-123"})
    monkeypatch.setattr(requests, "post", dummy_post)
    monkeypatch.setattr(requests, "get", dummy_get)
    dummy_result = Result(
        relates_to="test",
        result_name="TEST_RESULT",
        result_description="desc",
        details={"info": "detail"},
        formatted="formatted"
    )
    jira_instance.activate()
    jira_instance._create_task("Task Summary", "Task Description", "EPIC-123", dummy_result)
    assert called is True

def test_create_task_failure(jira_instance, monkeypatch):
    """
    Test that _create_task raises HTTPError when task creation fails.
    """
    def dummy_post(url, headers, data, timeout):
        return DummyResponse(400, text="Error")
    monkeypatch.setattr(requests, "post", dummy_post)
    monkeypatch.setattr(requests, "get", dummy_get)
    dummy_result = Result(
        relates_to="test",
        result_name="TEST_RESULT",
        result_description="desc",
        details={"info": "detail"},
        formatted="formatted"
    )
    with pytest.raises(requests.HTTPError):
        jira_instance.activate()
        jira_instance._create_task("Task Summary", "Task Description", "EPIC-123", dummy_result)

def test_append_details_to_task(jira_instance, monkeypatch, tmp_path):
    """
    Test that _append_details_to_task writes a temporary file with the correct details.
    Uses tmp_path to avoid writing to the actual filesystem.
    """
    # Change working directory to a temporary path.
    monkeypatch.chdir(tmp_path)
    def dummy_post(url, headers, files, timeout):
        return DummyResponse(200)
    monkeypatch.setattr(requests, "post", dummy_post)
    monkeypatch.setattr(requests, "get", dummy_get)
    dummy_result = Result(
        relates_to="test",
        result_name="TEST_RESULT",
        result_description="desc",
        details={"key": "value"},
        formatted="formatted"
    )
    jira_instance.activate()
    jira_instance._append_details_to_task("ISSUE-123", dummy_result)
    temp_file = tmp_path / "temp" / "TEST_RESULT.txt"
    assert temp_file.exists()
    with open(temp_file, "r") as f:
        content = json.loads(f.read())
    assert content == dummy_result.details

def test_proccess_results(jira_instance, monkeypatch):
    """
    Test that proccess_results processes each result by calling _generate_solution and _upload_plan.
    """
    dummy_plan = SolutionsPlan(epics=[])
    generate_called = False
    upload_called = False
    def dummy_generate(result):
        nonlocal generate_called
        generate_called = True
        return dummy_plan
    def dummy_upload(plan, result):
        nonlocal upload_called
        upload_called = True
    monkeypatch.setattr(jira_instance, "_generate_solution", dummy_generate)
    monkeypatch.setattr(jira_instance, "_upload_plan", dummy_upload)
    monkeypatch.setattr(requests, "get", dummy_get)
    dummy_result = Result(
        relates_to="test",
        result_name="TEST_RESULT",
        result_description="desc",
        details={"key": "value"},
        formatted="formatted"
    )
    jira_instance.activate()
    jira_instance.proccess_results([dummy_result])
    assert generate_called is True
    assert upload_called is True

def dummy_program(document: str):
    # Return a valid SolutionsPlan with an empty list of epics.
    return SolutionsPlan(epics=[])

def test_generate_solution_no_embed(jira_instance, monkeypatch):
    """
    Test _generate_solution branch when AppConfig().embed_model is None.
    Instead of using a dummy class, we return a dummy function that returns a valid SolutionsPlan.
    """

    # Instead of monkeypatching the AppConfig class, get the singleton instance and modify it.
    config_instance = AppConfig()
    config_instance.embed_model = None
    config_instance.llm = object()
    
    from llama_index.core.program import LLMTextCompletionProgram

    # Monkey-patch the factory method to return our dummy function.
    monkeypatch.setattr(LLMTextCompletionProgram, "from_defaults", lambda **kwargs: dummy_program)

    # Patch GET requests to avoid network calls.
    monkeypatch.setattr(requests, "get", dummy_get)

    dummy_result = Result(
        relates_to="test",
        result_name="TEST_RESULT",
        result_description="desc",
        details={"key": "value"},
        formatted="formatted"
    )
    jira_instance.activate()
    plan = jira_instance._generate_solution(dummy_result)

    # Check that the plan is a valid SolutionsPlan with an empty list of epics.
    assert plan is not None, "Expected _generate_solution to return a SolutionsPlan, got None"
    assert isinstance(plan, SolutionsPlan)
    assert plan.epics == []

