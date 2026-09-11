import json

import httpx
import pytest

from qa_pipeline.generation import prepare_generation
from qa_pipeline.retrieval import load_document
from qa_pipeline.model import GenerationError, generate


@pytest.fixture
def packet(tmp_path, monkeypatch):
    monkeypatch.setenv("QA_ENABLE_LIVE_MODEL", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "fake-test-key")
    monkeypatch.setenv("QA_MODEL", "test-model")
    source = tmp_path / "requirements.md"
    source.write_text("**AUTH-04** Guests can browse without a wallet.")
    return prepare_generation(load_document(source), "AUTH-04")


def reply(source_id="AUTH-04"):
    draft = {"scenarios": [{"title": "Guest browsing", "preconditions": [],
        "steps": [{"action": "Browse", "expected_result": "Browsing available"}],
        "source_ids": [source_id]}], "questions": []}
    return {"status": "completed", "output": [{"type": "message", "content": [
        {"type": "output_text", "text": json.dumps(draft)}]}],
        "usage": {"input_tokens": 100, "output_tokens": 50}}


def test_request_contract_and_validated_result(packet):
    calls = []
    def handler(request):
        calls.append(request)
        body = json.loads(request.content)
        assert str(request.url) == "https://api.openai.com/v1/responses"
        assert body["store"] is False
        assert body["max_output_tokens"] == 3000
        assert body["text"]["format"]["strict"] is True
        assert "AUTH-04" in body["input"]
        return httpx.Response(200, json=reply())
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = generate(packet, client=client)
    assert len(calls) == 1
    assert result["status"] == "needs_human_review"
    assert result["usage"]["output_tokens"] == 50


@pytest.mark.parametrize("case", ["disabled", "missing_key", "missing_model", "no_evidence", "oversized"])
def test_preflight_never_calls_provider(packet, monkeypatch, case):
    if case == "disabled":
        monkeypatch.delenv("QA_ENABLE_LIVE_MODEL")
    elif case == "missing_key":
        monkeypatch.delenv("OPENAI_API_KEY")
    elif case == "missing_model":
        monkeypatch.delenv("QA_MODEL")
    elif case == "no_evidence":
        packet["status"] = "no_evidence"
    else:
        packet["evidence"]["results"][0]["text"] = "x" * 33000
    def handler(request):
        pytest.fail("Preflight should prevent this request")
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(GenerationError):
            generate(packet, client=client)


@pytest.mark.parametrize("case", ["refusal", "incomplete", "bad_citation", "empty", "invalid_json", "rate_limit", "timeout"])
def test_failure_rejected_without_retry_or_secret_leak(packet, case):
    calls = []
    def handler(request):
        calls.append(request)
        body = reply()
        if case == "timeout":
            raise httpx.ReadTimeout("fake-test-key", request=request)
        if case == "rate_limit":
            return httpx.Response(429, text="fake-test-key")
        if case == "refusal":
            body["output"][0]["content"] = [{"type": "refusal", "refusal": "Declined"}]
        elif case == "incomplete":
            body["status"] = "incomplete"
        elif case == "bad_citation":
            body = reply("AUTH-99")
        elif case == "empty":
            body["output"] = []
        elif case == "invalid_json":
            return httpx.Response(200, text="fake-test-key")
        return httpx.Response(200, json=body)
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(GenerationError) as error:
            generate(packet, client=client)
    assert "fake-test-key" not in str(error.value)
    assert len(calls) == 1
