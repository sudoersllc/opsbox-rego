import pytest
from pydantic import BaseModel
import pandas as pd
import requests
from loguru import logger
import logging

# Import using relative (module) imports.
from .github import github
from .github.github import GithubOutput, Result # type: ignore


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

def get_test_config(create_description: bool = False, labels: str | None = None):
    config_model = GithubOutput().grab_config()
    return config_model(
        github_token="fake_token",
        repo_owner="owner",
        repo_name="repo",
        labels=labels,
        create_description=create_description,
    )

# A helper BaseModel for set_data
class FakeConfig(BaseModel):
    github_token: str
    repo_owner: str
    repo_name: str
    labels: str | None = None
    create_description: bool = False

# A fake result instance.
def fake_result():
    return Result(
        relates_to="fake_service",
        result_name="fake_result",
        result_description="A fake result",
        details={"foo": "bar"},
        formatted="This is a test formatted result"
    )

# A fake response class to simulate requests.post responses.
class FakeResponse:
    def __init__(self, status_code, json_data=None):
        self.status_code = status_code
        self._json = json_data or {}

    def json(self):
        return self._json

def test_grab_config():
    gh_out = GithubOutput()
    ConfigModel = gh_out.grab_config()
    # Check that the returned config model is a subclass of BaseModel.
    assert issubclass(ConfigModel, BaseModel)
    # Instantiate and check fields.
    config = ConfigModel(
        github_token="fake_token",
        repo_owner="owner",
        repo_name="repo",
        labels="bug,enhancement",
        create_description=True,
    )
    assert config.github_token == "fake_token"
    assert config.repo_owner == "owner"
    assert config.repo_name == "repo"
    assert config.labels == "bug,enhancement"
    assert config.create_description is True

def test_set_data():
    gh_out = GithubOutput()
    config = get_test_config()
    gh_out.set_data(config)
    # Check that the model and credentials are stored correctly.
    assert gh_out.model == config
    # credentials should be a dict (the output of model_dump)
    assert isinstance(gh_out.credentials, dict)
    assert gh_out.credentials["github_token"] == "fake_token"

def test_proccess_results_raw(monkeypatch, loguru_caplog):
    gh_out = GithubOutput()
    config = get_test_config(create_description=False, labels=None)
    gh_out.set_data(config)
    result = fake_result()

    # Fake requests.post: it is called twice.
    # First call is to create the Gist.
    # Second call is to create the GitHub issue.
    call_count = {"post": 0}
    def fake_post(url, **kwargs):
        call_count["post"] += 1
        # For Gist creation endpoint.
        if "gists" in url:
            # Simulate successful gist creation.
            return FakeResponse(201, json_data={"html_url": "https://gist.github.com/fake_gist"})
        elif "repos" in url:
            # Check that the issue payload uses the raw formatted result.
            data = kwargs.get("json")
            expected_title = f'OpsBox Optimization Check - {pd.Timestamp.now().strftime("%Y-%m-%d")} - {result.result_name}'
            # We expect the body to equal result.formatted.
            assert data["body"] == result.formatted
            # Labels should default to [] if not provided.
            assert data["labels"] == []
            # And routing_key should come from configuration.
            assert data["title"] == expected_title
            # (Note: the URL is built using repo_owner and repo_name from config.)
            return FakeResponse(201, json_data={"html_url": "https://github.com/fake_issue"})
        else:
            return FakeResponse(400)
    monkeypatch.setattr(requests, "post", fake_post)

    gh_out.proccess_results([result])
    # Expect a success message from issue creation.
    assert "Successfully created issue:" in loguru_caplog.text
    # Also, the Gist creation branch should have logged a success.
    assert call_count["post"] == 2

# Test the branch when create_description is True and embed_model is None (LLM branch)
def test_proccess_results_create_description_no_embed(monkeypatch, loguru_caplog):
    gh_out = GithubOutput()
    config = get_test_config(create_description=True)
    gh_out.set_data(config)
    result = fake_result()

    # Patch AppConfig to simulate embed_model is None.
    class FakeAppConfigNoEmbed:
        def __init__(self):
            self.embed_model = None
            self.llm = "unused_llm"
    monkeypatch.setattr(github, "AppConfig", lambda: FakeAppConfigNoEmbed())

    # Patch LLMTextCompletionProgram.from_defaults to return a fake program.
    class FakeLLMResponse:
        # Simulate a response with choices list.
        def __init__(self, text):
            self.choices = [type("FakeChoice", (), {"text": text})]
    def fake_llm_program(**kwargs):
        def inner(document):
            # Return a fake LLM response object.
            return FakeLLMResponse("LLM generated issue body")
        return inner
    monkeypatch.setattr(github, "LLMTextCompletionProgram",
                        type("FakeLLM", (), {"from_defaults": staticmethod(fake_llm_program)}))

    # For Gist creation and issue creation, patch requests.post accordingly.
    def fake_post(url, **kwargs):
        if "gists" in url:
            # Simulate successful gist creation.
            return FakeResponse(201, json_data={"html_url": "https://gist.github.com/fake_gist"})
        elif "repos" in url:
            # For issue creation: check that the issue body equals the LLM response.
            data = kwargs.get("json")
            # The LLM branch does not append extra text.
            assert data["body"] == "LLM generated issue body"
            return FakeResponse(201, json_data={"html_url": "https://github.com/fake_issue"})
        return FakeResponse(400)
    monkeypatch.setattr(requests, "post", fake_post)

    gh_out.proccess_results([result])
    assert "Successfully created issue:" in loguru_caplog.text

# Test the branch when create_description is True and embed_model is not None (vector branch)
def test_proccess_results_create_description_with_embed(monkeypatch, loguru_caplog):
    gh_out = GithubOutput()
    config = get_test_config(create_description=True)
    gh_out.set_data(config)
    result = fake_result()

    # Patch AppConfig to simulate embed_model present.
    class FakeAppConfigWithEmbed:
        def __init__(self):
            self.embed_model = object()  # non-None triggers vector branch
            self.llm = "fake_llm"
    monkeypatch.setattr(github, "AppConfig", lambda: FakeAppConfigWithEmbed())

    # Patch VectorStoreIndex.from_documents to simulate a query engine.
    def fake_from_documents(docs, embed_model):
        class FakeIndex:
            def as_query_engine(self, llm):
                class FakeQueryEngine:
                    def query(self, query):
                        # Return a fake query result string.
                        return "Vector generated issue body"
                return FakeQueryEngine()
        return FakeIndex()
    monkeypatch.setattr(github, "VectorStoreIndex",
                        type("FakeVectorStoreIndex", (), {"from_documents": staticmethod(fake_from_documents)}))

    # Patch requests.post to simulate successful responses.
    def fake_post(url, **kwargs):
        if "gists" in url:
            return FakeResponse(201, json_data={"html_url": "https://gist.github.com/fake_gist"})
        elif "repos" in url:
            data = kwargs.get("json")
            # In the vector branch, the issue body is the vector query result plus a line with the gist URL.
            expected_body = "Vector generated issue body" + "\n\nThe detailed formatted result can be found here: https://gist.github.com/fake_gist"
            assert data["body"] == expected_body
            return FakeResponse(201, json_data={"html_url": "https://github.com/fake_issue"})
        return FakeResponse(400)
    monkeypatch.setattr(requests, "post", fake_post)

    gh_out.proccess_results([result])
    assert "Successfully created issue:" in loguru_caplog.text

# Test that when Gist creation fails, errors are logged.
def test_gist_failure(monkeypatch, loguru_caplog):
    gh_out = GithubOutput()
    config = get_test_config(create_description=False)
    gh_out.set_data(config)
    result = fake_result()

    def fake_post(url, **kwargs):
        if "gists" in url:
            # Simulate failure with status code 400.
            return FakeResponse(400, json_data={"message": "Bad Request"})
        elif "repos" in url:
            return FakeResponse(201, json_data={"html_url": "https://github.com/fake_issue"})
        return FakeResponse(400)
    monkeypatch.setattr(requests, "post", fake_post)

    with loguru_caplog.at_level("ERROR"):
        gh_out.proccess_results([result])
    # Check that an error message regarding gist creation is logged.
    assert "Failed to create Gist:" in loguru_caplog.text

# Test that if an exception occurs, the plugin logs an error.
def test_proccess_results_exception(monkeypatch, loguru_caplog):
    gh_out = GithubOutput()
    config = get_test_config(create_description=False)
    gh_out.set_data(config)
    result = fake_result()

    def fake_post(url, **kwargs):
        raise Exception("Test exception")
    monkeypatch.setattr(requests, "post", fake_post)

    with loguru_caplog.at_level("ERROR"):
        gh_out.proccess_results([result])
    # Check that an error message about failing to send results is logged.
    assert "Failed to send results via GitHub Tickets:" in loguru_caplog.text
