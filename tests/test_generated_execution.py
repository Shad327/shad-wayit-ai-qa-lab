import hashlib
import json
from pathlib import Path

import pytest
from qa_pipeline.run_generated import execute


def test_wrong_code_approval_creates_no_artifacts(tmp_path):
    with pytest.raises(ValueError):
        execute({'code': '# test'}, 'wrong', tmp_path)
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize('exit_code,state', [(0,'passed'),(1,'failed'),(2,'error')])
def test_artifact_identity_and_environment(tmp_path, monkeypatch, exit_code, state):
    code = 'def test_example():\n    assert True\n'
    monkeypatch.setenv('OPENAI_API_KEY', 'secret')
    class Process:
        def __init__(self, command, **kwargs):
            assert 'OPENAI_API_KEY' not in kwargs['env']
            assert '--confcutdir' in command
            assert Path(command[7]).read_text() == code
        def wait(self, timeout=None):
            return exit_code
        def poll(self):
            return exit_code
    monkeypatch.setattr('qa_pipeline.run_generated.subprocess.Popen', Process)
    folder, manifest = execute({'code':code,'package_sha256':'source-package'}, hashlib.sha256(code.encode()).hexdigest(), tmp_path)
    assert manifest['state'] == state
    assert json.loads((folder/'manifest.json').read_text())['package_sha256'] == 'source-package'
    assert (folder/'test_approved_guest_features.py').read_text() == code
