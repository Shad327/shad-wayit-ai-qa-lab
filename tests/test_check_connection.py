import json

import httpx
import pytest

from qa_pipeline.check_connection import check_connection


@pytest.fixture(autouse=True)
def configure(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-private-test-secret")
    monkeypatch.setenv("QA_MODEL", "gpt-5-mini")


@pytest.mark.parametrize("probe", [False, True])
def test_bounded_request(probe):
    calls = []
    def handler(request):
        calls.append(request)
        assert request.headers["authorization"] == "Bearer sk-private-test-secret"
        if probe:
            assert request.method == "POST"
            payload = json.loads(request.content)
            assert payload == {"model": "gpt-5-mini", "input": "Reply OK.", "store": False, "max_output_tokens": 16}
        else:
            assert request.method == "GET"
            assert request.url.path == "/v1/models/gpt-5-mini"
        return httpx.Response(200, json={"status": "incomplete"})
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        report = check_connection(probe=probe, client=client)
    assert len(calls) == 1
    assert report["status"] == ("generation_reachable" if probe else "lookup_only_passed")


def test_error_redaction_and_request_id():
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(404, headers={"x-request-id": "req_test"}, json={"error": {
            "code": "model_not_found", "message": "Rejected sk-private-test-secret and sk-other-secret"}})
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        report = check_connection(probe=True, client=client)
    assert len(calls) == 1
    assert report["code"] == "model_not_found"
    assert report["x-request-id"] == "req_test"
    assert "sk-" not in json.dumps(report)


def test_missing_key_never_calls(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY")
    def handler(request):
        pytest.fail("Must not call without configuration")
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        assert check_connection(client=client)["status"] == "configuration_missing"


def test_network_error_does_not_leak_or_retry():
    calls = []
    def handler(request):
        calls.append(request)
        raise httpx.ReadTimeout("sk-private-test-secret", request=request)
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        report = check_connection(probe=True, client=client)
    assert len(calls) == 1
    assert report["status"] == "network_error"
    assert "sk-" not in json.dumps(report)
