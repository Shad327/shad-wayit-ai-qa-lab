import json

import pytest
from fastapi.testclient import TestClient

from qa_pipeline.api import create_app
from qa_pipeline.generation import prepare_generation, validate_draft
from qa_pipeline.retrieval import load_document


@pytest.fixture
def source(tmp_path):
    path = tmp_path / "requirements.md"
    path.write_text("# Guests\n**AUTH-04** Guests may browse without a wallet.\n")
    return path


@pytest.fixture
def packet(source):
    return prepare_generation(load_document(source), "AUTH-04")


@pytest.fixture
def draft():
    # Hand-written test fixture, not an LLM-generated scenario.
    return {"scenarios": [{"title": "Guest browsing", "preconditions": ["No wallet connected"],
        "steps": [{"action": "Open browsing page", "expected_result": "Content is visible"}],
        "source_ids": ["AUTH-04"]}], "questions": ["What is the browsing page URL?"]}


def test_prepare_api_returns_real_evidence_without_model_call(source):
    response = TestClient(create_app(source)).post("/generation/prepare", json={"query": "AUTH-04"})
    assert response.status_code == 200
    packet = response.json()
    assert packet["status"] == "ready_for_model"
    assert packet["model_called"] is False
    assert packet["evidence"]["results"][0]["text"].endswith("without a wallet.")
    assert packet["response_schema"]["additionalProperties"] is False


def test_no_evidence_blocks_validation(source, draft):
    packet = prepare_generation(load_document(source), "AUTH-99")
    assert packet["status"] == "no_evidence"
    with pytest.raises(ValueError, match="without evidence"):
        validate_draft(json.dumps(draft), packet)


def test_valid_draft_still_requires_human_review(packet, draft):
    result = validate_draft(json.dumps(draft), packet)
    assert result["status"] == "needs_human_review"
    assert result["evidence"][0]["document_sha256"]
    assert result["checks"] == ["schema_valid", "citation_ids_exist"]


def test_unretrieved_reference_rejected(packet, draft):
    draft["scenarios"][0]["source_ids"] = ["AUTH-99"]
    with pytest.raises(ValueError, match="not retrieved"):
        validate_draft(json.dumps(draft), packet)


@pytest.mark.parametrize("change", ["empty_steps", "empty_sources", "blank_title", "extra_code", "no_scenarios"])
def test_invalid_structure_rejected(packet, draft, change):
    scenario = draft["scenarios"][0]
    if change == "empty_steps":
        scenario["steps"] = []
    elif change == "empty_sources":
        scenario["source_ids"] = []
    elif change == "blank_title":
        scenario["title"] = "   "
    elif change == "extra_code":
        scenario["code"] = "print('unapproved')"
    else:
        draft["scenarios"] = []
    with pytest.raises(ValueError):
        validate_draft(json.dumps(draft), packet)


@pytest.mark.parametrize("raw", ["not json", "x" * 100001])
def test_malformed_or_oversized_response_rejected(packet, raw):
    with pytest.raises(ValueError):
        validate_draft(raw, packet)
