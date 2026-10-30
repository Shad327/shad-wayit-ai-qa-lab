from fastapi.testclient import TestClient
from qa_pipeline.api import create_app


def test_evidence_snapshot_preserves_edits_and_blocks_stale_approval(tmp_path):
    source = tmp_path / "requirements.md"
    source.write_text("**AUTH-04** Guests can browse without a wallet.")
    client = TestClient(create_app(source, tmp_path / "reviews.sqlite3"))
    url = "/reviews/AUTH-04"
    first = client.post(url + "/from-evidence", json={"revision":0}).json()["review"]
    assert first["mode"] == "demo_data"
    assert first["evidence"][0]["id"] == "AUTH-04"
    assert first["revision"] == 1
    edit = client.put(url, json={"revision":1,"scenario":"My reviewed scenario"}).json()["review"]
    assert edit["evidence"] == first["evidence"]
    assert client.post(url + "/approve", json={"revision":2}).status_code == 200
    source.write_text("**AUTH-04** Updated browsing policy.")
    read = client.get(url).json()["review"]
    assert read["evidence_stale"] and not read["approved"]
    assert client.post(url + "/approve", json={"revision":2}).status_code == 409
    refreshed = client.post(url + "/from-evidence", json={"revision":2}).json()["review"]
    assert refreshed["scenario"] == "My reviewed scenario"
    assert refreshed["revision"] == 3 and not refreshed["approved"]
    assert refreshed["evidence"][0]["document_sha256"] != first["evidence"][0]["document_sha256"]


def test_no_evidence_creates_no_sample(tmp_path):
    source = tmp_path / "requirements.md"
    source.write_text("**AUTH-99** Unrelated.")
    client = TestClient(create_app(source, tmp_path / "reviews.sqlite3"))
    assert client.post("/reviews/AUTH-04/from-evidence", json={"revision":0}).status_code == 409
    assert client.get("/reviews/AUTH-04").json()["review"] is None
