"""Run a supported approved template from the local review store.

Preview first, then pass the printed SHA-256 using --approve-code.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
from uuid import uuid4

from .retrieval import load_document
from .structured_reviews import StructuredReviews
from .test_generation import generate_preview


def execute(preview, approved_hash, output_root, timeout=180):
    code = preview['code']
    fingerprint = hashlib.sha256(code.encode()).hexdigest()
    if approved_hash != fingerprint:
        raise ValueError('Code approval does not match the current generated test. Preview again.')
    directory = Path(output_root) / ('generated-' + str(uuid4()))
    directory.mkdir(parents=True)
    test = directory / 'test_approved_guest_features.py'
    test.write_text(code)
    manifest = {**preview, 'code_sha256': fingerprint, 'state': 'running', 'executed': False}
    manifest_path = directory / 'manifest.json'
    manifest_path.write_text(json.dumps(manifest, indent=2))
    # Separate directory/config prevents portfolio browser fixtures from changing this test.
    config = directory / 'pytest.ini'
    config.write_text('[pytest]\n')
    command = [sys.executable, '-m', 'pytest', '-c', str(config.resolve()),
               '--confcutdir', str(directory.resolve()), str(test.resolve()),
               '--browser', 'chromium', '--screenshot', 'on', '--tracing', 'on',
               '--output', str((directory / 'artifacts').resolve()),
               '--junitxml', str((directory / 'results.xml').resolve()), '-v']
    env = {key: os.environ[key] for key in ('HOME','PATH','TMPDIR','LANG','PLAYWRIGHT_BROWSERS_PATH') if key in os.environ}
    process = None
    try:
        with (directory / 'run.log').open('w') as log:
            process = subprocess.Popen(command, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            manifest['executed'] = True
            result = process.wait(timeout=timeout)
            manifest.update(exit_code=result, state='passed' if result == 0 else 'failed' if result == 1 else 'error')
    except subprocess.TimeoutExpired:
        manifest['state'] = 'timed_out'
    except (OSError, KeyboardInterrupt):
        manifest['state'] = 'interrupted' if process else 'error'
    finally:
        if process and process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
        manifest_path.write_text(json.dumps(manifest, indent=2))
    return directory, manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision', type=int, required=True)
    parser.add_argument('--approve-code', help='SHA-256 printed by preview; omitting this only previews')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    source = Path(os.environ.get('QA_REQUIREMENTS_PATH', root / 'outputs/requirements.md'))
    passages = load_document(source)
    exported = StructuredReviews(root / 'outputs/reviews.sqlite3').export('AUTH-04', args.revision, passages[0].document_sha256 if passages else None)
    preview = generate_preview(exported)
    digest = hashlib.sha256(preview['code'].encode()).hexdigest()
    if not args.approve_code:
        print(preview['code'])
        print('Code SHA-256:', digest)
        print('Template-generated; not executed. Review code before supplying --approve-code.')
        return
    directory, manifest = execute(preview, args.approve_code, root / 'outputs')
    print(json.dumps({'directory': str(directory), 'state': manifest['state']}, indent=2))
    raise SystemExit(0 if manifest['state'] == 'passed' else 1)


if __name__ == '__main__':
    main()
