import json
from uuid import uuid4

import pytest
from fastapi import HTTPException
from qa_pipeline.generated_jobs import GeneratedRunManager


def test_generated_runner_saves_exact_plan_and_rechecks(tmp_path, monkeypatch):
    preview = {'code':'def test_public():\n    assert True\n', 'revision':1, 'package_sha256':'a'*64}
    monkeypatch.setattr('qa_pipeline.generated_jobs.generate_preview', lambda _: dict(preview))
    manager = GeneratedRunManager(tmp_path, tmp_path/'runs.sqlite3', lambda: {})
    plan = manager.plan()
    with pytest.raises(HTTPException):
        manager.enqueue(uuid4(), plan['hash'], False, dispatch=False)
    row = manager.enqueue(uuid4(), plan['hash'], True, dispatch=False)
    artifact = tmp_path / ('generated-web-'+row['id']);artifact.mkdir()
    args = manager.test_arguments(artifact)
    assert '--confcutdir' in args
    assert (artifact/'test_approved_guest_features.py').read_text() == preview['code']
    assert json.loads((artifact/'manifest.json').read_text())['hash'] == plan['hash']
    preview['revision'] = 2
    with pytest.raises(HTTPException):
        manager.test_arguments(artifact)
    monkeypatch.setattr('qa_pipeline.jobs.subprocess.Popen', lambda *a, **k: pytest.fail('Must not launch stale plan'))
    manager.execute(row['id'])
    assert manager.get(row['id'])['state'] == 'error'


def test_history_is_bounded_and_newest_first(tmp_path):
    manager = GeneratedRunManager(tmp_path, tmp_path/'runs.sqlite3', lambda: {})
    assert manager.history() == []
    with manager.connection() as db:
        for index in range(12):
            db.execute('INSERT INTO runs (id,state,plan_hash,approved_at) VALUES (?,?,?,?)',
                       (str(uuid4()), 'passed', 'a'*64, f'2026-09-13T10:{index:02d}:00'))
    history = manager.history()
    assert len(history) == 10
    assert history[0]['approved_at'].endswith('10:11:00')
    assert history[-1]['approved_at'].endswith('10:02:00')
