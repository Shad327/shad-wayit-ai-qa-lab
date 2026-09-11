import pytest
from fastapi.testclient import TestClient

from qa_pipeline.api import create_app


@pytest.fixture
def client(tmp_path):
    source = tmp_path / "requirements.md"
    source.write_text("# Test PRD\n**Document version:** 1.0\n\n## Guests\n**AUTH-04** Browse without a wallet.\n")
    return TestClient(create_app(source))


def test_retrieval_contract_returns_original_evidence(client):
    response = client.post("/retrieve", json={"query": "AUTH-04", "limit": 1})
    assert response.status_code == 200
    body = response.json()
    assert body["method"] == "lexical_baseline"
    assert body["results"][0]["text"] == "**AUTH-04** Browse without a wallet."
    assert body["results"][0]["start_line"] == 5
    assert len(body["results"][0]["document_sha256"]) == 64


@pytest.mark.parametrize("body", [{"query": " "}, {"query": "x" * 2001}, {"query": "wallet", "limit": True},
    {"query": "wallet", "limit": 11}, {"query": "wallet", "source": "/etc/passwd"}, {"query": 42}])
def test_invalid_requests_rejected(client, body):
    assert client.post("/retrieve", json=body).status_code == 422


def test_no_match_is_successful_empty_search(client):
    response = client.post("/retrieve", json={"query": "AUTH-99"})
    assert response.status_code == 200
    assert response.json()["status"] == "no_evidence"


def test_missing_source_does_not_expose_filesystem_path(tmp_path):
    client = TestClient(create_app(tmp_path / "private-name.md"))
    response = client.post("/retrieve", json={"query": "wallet"})
    assert response.status_code == 503
    assert "private-name" not in response.text
    assert client.get("/health").status_code == 503


def test_source_edits_are_visible_next_request(tmp_path):
    source = tmp_path / "requirements.md"
    source.write_text("**AUTH-04** First policy")
    client = TestClient(create_app(source))
    first = client.post("/retrieve", json={"query": "AUTH-04"}).json()["results"][0]
    source.write_text("**AUTH-04** Revised policy")
    second = client.post("/retrieve", json={"query": "AUTH-04"}).json()["results"][0]
    assert second["text"].endswith("Revised policy")
    assert first["document_sha256"] != second["document_sha256"]


def test_unexpected_host_is_rejected(client):
    assert client.get("/health", headers={"host": "unexpected.example"}).status_code == 400


def test_health_reports_actual_document_readiness(client):
    assert client.get("/health").json() == {"status": "ready", "method": "lexical_baseline", "passages": 2, "model_calls": False}
