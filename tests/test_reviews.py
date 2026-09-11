import pytest
from fastapi.testclient import TestClient
from qa_pipeline.api import create_app


@pytest.fixture
def client(tmp_path):
    return TestClient(create_app(review_path=tmp_path / "reviews.sqlite3"))


def save(client, text="Check navigation", revision=0):
    return client.put("/reviews/AUTH-04", json={"scenario": text, "revision": revision})


def test_saved_approval_survives_new_app(tmp_path):
    path = tmp_path / "reviews.sqlite3"
    first = TestClient(create_app(review_path=path))
    assert save(first).json()["review"]["mode"] == "demo_data"
    assert first.post("/reviews/AUTH-04/approve", json={"revision": 1}).status_code == 200
    second = TestClient(create_app(review_path=path))
    row = second.get("/reviews/AUTH-04").json()["review"]
    assert row["approved"] and row["approved_at"]
    assert row["scenario"] == "Check navigation"


def test_edit_invalidates_approval(client):
    save(client)
    client.post("/reviews/AUTH-04/approve", json={"revision": 1})
    row = save(client, "Check keyboard", 1).json()["review"]
    assert row["revision"] == 2
    assert not row["approved"] and row["approved_at"] is None
    assert client.post("/reviews/AUTH-04/approve", json={"revision": 1}).status_code == 409


def test_stale_save_cannot_overwrite(client):
    save(client)
    assert save(client, "Stale edit").status_code == 409
    assert client.get("/reviews/AUTH-04").json()["review"]["scenario"] == "Check navigation"


def test_missing_review_cannot_be_approved(client):
    assert client.get("/reviews/AUTH-04").json() == {"review": None}
    assert client.post("/reviews/AUTH-04/approve", json={"revision": 0}).status_code == 409


@pytest.mark.parametrize("data", [{"scenario": " ", "revision": 0}, {"scenario": "x" * 8001, "revision": 0}, {"scenario": "x", "revision": True}, {"scenario": "x", "revision": 0, "approved": True}])
def test_invalid_edits_rejected(client, data):
    assert client.put("/reviews/AUTH-04", json=data).status_code == 422


def test_cross_origin_write_rejected(client):
    response = client.put("/reviews/AUTH-04", headers={"Origin": "https://untrusted.example"}, json={"scenario": "x", "revision": 0})
    assert response.status_code == 403


def test_storage_failure_has_safe_error(tmp_path):
    path = tmp_path / "not-a-directory"
    path.write_text("file")
    client = TestClient(create_app(review_path=path / "reviews.sqlite3"))
    response = client.get("/reviews/AUTH-04")
    assert response.status_code == 503
    assert str(path) not in response.text
