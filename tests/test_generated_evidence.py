from uuid import uuid4
from qa_pipeline.generated_evidence import evidence_files


def test_missing_files_and_failed_screenshot_priority(tmp_path):
    identifier = uuid4()
    assert evidence_files(tmp_path, identifier) == {}
    folder = tmp_path / f'generated-web-{identifier}' / 'artifacts' / 'test-approved-guest-features-py-test-approved-guest-features-chromium'
    folder.mkdir(parents=True)
    (folder/'test-finished-1.png').write_bytes(b'finished')
    (folder/'test-failed-1.png').write_bytes(b'failed')
    (folder/'trace.zip').write_bytes(b'trace')
    files = evidence_files(tmp_path, identifier)
    assert files['screenshot'].read_bytes() == b'failed'
    assert files['trace'].read_bytes() == b'trace'


def test_symlink_outside_output_is_not_served(tmp_path):
    root = tmp_path/'outputs';root.mkdir()
    identifier = uuid4()
    folder = root / f'generated-web-{identifier}' / 'artifacts' / 'test-approved-guest-features-py-test-approved-guest-features-chromium'
    folder.mkdir(parents=True)
    secret = tmp_path/'secret';secret.write_text('private')
    (folder/'trace.zip').symlink_to(secret)
    assert evidence_files(root, identifier) == {}
