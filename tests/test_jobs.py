from pathlib import Path
from uuid import uuid4

import pytest
from fastapi import HTTPException

from qa_pipeline.jobs import RunManager


@pytest.fixture
def manager(tmp_path):
    (tmp_path / "browser_tests").mkdir()
    (tmp_path / "browser_tests/test_noiselabz.py").write_text("# fixed test suite")
    (tmp_path / "browser_tests/conftest.py").write_text("# fixtures")
    (tmp_path / "pyproject.toml").write_text("# config")
    return RunManager(tmp_path, tmp_path / "runs.sqlite3")


def test_requires_current_plan_and_explicit_approval(manager):
    with pytest.raises(HTTPException) as error:
        manager.enqueue(uuid4(), manager.plan()["hash"], False, dispatch=False)
    assert error.value.status_code == 422
    with pytest.raises(HTTPException) as error:
        manager.enqueue(uuid4(), "a" * 64, True, dispatch=False)
    assert error.value.status_code == 409


def test_idempotency_and_overlapping_runs(manager):
    identifier = uuid4()
    plan = manager.plan()["hash"]
    first = manager.enqueue(identifier, plan, True, dispatch=False)
    assert manager.enqueue(identifier, plan, True, dispatch=False) == first
    with pytest.raises(HTTPException) as error:
        manager.enqueue(uuid4(), plan, True, dispatch=False)
    assert error.value.status_code == 409


def test_restart_marks_unfinished_run_interrupted(manager):
    row = manager.enqueue(uuid4(), manager.plan()["hash"], True, dispatch=False)
    manager.recover()
    assert manager.get(row["id"])["state"] == "interrupted"


def test_suite_change_before_execution_blocks_launch(manager, monkeypatch):
    row = manager.enqueue(uuid4(), manager.plan()["hash"], True, dispatch=False)
    (manager.root / "browser_tests/test_noiselabz.py").write_text("# changed")
    monkeypatch.setattr("qa_pipeline.jobs.subprocess.Popen", lambda *a, **k: pytest.fail("Must not launch"))
    manager.execute(row["id"])
    assert manager.get(row["id"])["state"] == "error"


@pytest.mark.parametrize("exit_code,state", [(0,"passed"),(1,"failed"),(2,"error"),(5,"error")])
def test_execution_uses_fixed_command_without_model_secrets(manager, monkeypatch, exit_code, state):
    monkeypatch.setenv("OPENAI_API_KEY", "never-pass-to-browser")
    class Process:
        def __init__(self, args, **kwargs):
            assert args[3] == "browser_tests/test_noiselabz.py"
            assert kwargs["cwd"] == manager.root
            assert "OPENAI_API_KEY" not in kwargs["env"]
            assert kwargs["start_new_session"]
            Path(args[-1]).write_text("<testsuite/>")
        def wait(self, timeout=None):
            return exit_code
        def poll(self):
            return exit_code
    monkeypatch.setattr("qa_pipeline.jobs.subprocess.Popen", Process)
    row = manager.enqueue(uuid4(), manager.plan()["hash"], True, dispatch=False)
    manager.execute(row["id"])
    saved = manager.get(row["id"])
    assert saved["state"] == state
    assert saved["report"].endswith(".xml")
