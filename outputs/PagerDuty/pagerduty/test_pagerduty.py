import json
import pytest
from pydantic import BaseModel
import requests
from loguru import logger
import logging

from . import pagerDuty
from .pagerDuty import PagerDutyOutput, Result

class FakeModel(BaseModel):
    routing_key: str = "fake_routing_key"
    create_description: bool = False
    manual_severity: str | None = "low"

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

# A fake response to simulate requests.post
class FakeResponse:
    def __init__(self, status_code, text=""):
        self.status_code = status_code
        self.text = text

# Helper to create a fake Result instance.
def fake_result():
    return Result(
        relates_to="fake_service",
        result_name="fake_result",
        result_description="A fake result",
        details={"foo": "bar"},
        formatted="This is a test formatted result"
    )

def test_grab_config():
    pd_out = PagerDutyOutput()
    ConfigModel = pd_out.grab_config()
    assert issubclass(ConfigModel, BaseModel)
    config = ConfigModel(
        routing_key="test_key",
        create_description=False,
        manual_severity="high",
    )
    assert config.routing_key == "test_key"
    assert config.create_description is False
    assert config.manual_severity == "high"

def test_set_data():
    pd_out = PagerDutyOutput()
    fake_model_inst = FakeModel(routing_key="test_rk", create_description=False, manual_severity="medium")
    pd_out.set_data(fake_model_inst)
    assert pd_out.model == fake_model_inst
    assert pd_out.credentials == fake_model_inst.model_dump()

def test_proccess_results_manual(monkeypatch, capsys):
    pd_out = PagerDutyOutput()
    config_data = {"routing_key": "test_rk", "create_description": False, "manual_severity": "critical"}
    fake_model_inst = FakeModel(**config_data)
    pd_out.set_data(fake_model_inst)
    result = fake_result()

    def fake_post(url, data, headers, timeout):
        payload_sent = json.loads(data)
        expected_payload = {
            "summary": result.formatted,
            "severity": config_data["manual_severity"],
            "source": result.relates_to,
        }
        assert payload_sent["payload"] == expected_payload
        assert payload_sent["routing_key"] == fake_model_inst.routing_key
        assert payload_sent["event_action"] == "trigger"
        return FakeResponse(202)

    monkeypatch.setattr(requests, "post", fake_post)
    pd_out.proccess_results([result])
    captured = capsys.readouterr().out
    assert "Incident triggered successfully!" in captured

def test_proccess_results_vector(monkeypatch, capsys):
    pd_out = PagerDutyOutput()
    config_data = {"routing_key": "test_rk", "create_description": True, "manual_severity": "critical"}
    fake_model_inst = FakeModel(**config_data)
    pd_out.set_data(fake_model_inst)
    result = fake_result()

    # Use relative imports: patch AppConfig on the imported pagerDuty module.
    class FakeAppConfig:
        def __init__(self):
            self.embed_model = object()  # non-None triggers vector branch.
            self.llm = "fake_llm"
    monkeypatch.setattr(pagerDuty, "AppConfig", lambda: FakeAppConfig())

    # Patch VectorStoreIndex.from_documents via the relative module.
    def fake_from_documents(docs, embed_model):
        class FakeIndex:
            def as_query_engine(self, llm):
                class FakeQueryEngine:
                    def query(self, query):
                        fake_payload = {
                            "payload": {
                                "summary": "Vector summary",
                                "severity": "critical",
                                "source": "Vector source",
                            }
                        }
                        return json.dumps(fake_payload)
                return FakeQueryEngine()
        return FakeIndex()
    # Patch the VectorStoreIndex attribute on pagerDuty.
    monkeypatch.setattr(pagerDuty, "VectorStoreIndex",
                        type("FakeVectorStoreIndex", (), {"from_documents": staticmethod(fake_from_documents)}))

    def fake_post(url, data, headers, timeout):
        payload_sent = json.loads(data)
        expected_payload = {
            "summary": "Vector summary",
            "severity": "critical",
            "source": "Vector source",
        }
        assert payload_sent["payload"] == expected_payload
        assert payload_sent["routing_key"] == fake_model_inst.routing_key
        assert payload_sent["event_action"] == "trigger"
        return FakeResponse(202)
    monkeypatch.setattr(requests, "post", fake_post)

    pd_out.proccess_results([result])
    captured = capsys.readouterr().out
    assert "Incident triggered successfully!" in captured

def test_proccess_results_exception(monkeypatch, loguru_caplog):
    pd_out = PagerDutyOutput()
    config_data = {"routing_key": "test_rk", "create_description": False, "manual_severity": "critical"}
    fake_model_inst = FakeModel(**config_data)
    pd_out.set_data(fake_model_inst)
    result = fake_result()

    def fake_post(url, data, headers, timeout):
        raise Exception("Test exception")
    monkeypatch.setattr(requests, "post", fake_post)

    with loguru_caplog.at_level("ERROR"):
        pd_out.proccess_results([result])
    # Verify that a logger.error message with "Error sending Pagerduty:" is recorded.
    assert "Error sending Pagerduty:" in loguru_caplog.text

def test_proccess_results_create_description_no_embed(monkeypatch, loguru_caplog):
    pd_out = PagerDutyOutput()
    config_data = {"routing_key": "test_rk", "create_description": True, "manual_severity": "critical"}
    fake_model_inst = FakeModel(**config_data)
    pd_out.set_data(fake_model_inst)
    result = fake_result()

    # Patch AppConfig (relative import) to simulate embed_model == None.
    class FakeAppConfigNoEmbed:
        def __init__(self):
            self.embed_model = None
            self.llm = "unused_llm"
    monkeypatch.setattr(pagerDuty, "AppConfig", lambda: FakeAppConfigNoEmbed())

    # Patch LLMTextCompletionProgram.from_defaults using a relative patch.
    def fake_program(**kwargs):
        def inner(document):
            return '{"payload": {"summary": "LLM summary", "severity": "critical", "source": "LLM source"}}'
        return inner
    monkeypatch.setattr(pagerDuty, "LLMTextCompletionProgram",
                        type("FakeLLM", (), {"from_defaults": staticmethod(fake_program)}))


    def fake_post(url, data, headers, timeout):
        payload_sent = json.loads(data)
        expected_payload = {
            "summary": "LLM summary",
            "severity": "critical",
            "source": "LLM source",
        }
        assert payload_sent["payload"] == expected_payload
        return FakeResponse(202)
    monkeypatch.setattr(requests, "post", fake_post)

    pd_out.proccess_results([result])
    assert "Results sent via Pagerduty!" in loguru_caplog.text
