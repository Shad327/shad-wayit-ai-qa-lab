"""Allowlisted artifacts for supported generated browser tests."""
from pathlib import Path
from uuid import UUID


def evidence_files(output_root: Path, identifier: UUID):
    root = output_root.resolve()
    artifacts = root / f'generated-web-{identifier}' / 'artifacts'
    found = {}
    names_by_kind = {'screenshot': ['test-failed-1.png', 'test-finished-1.png'], 'trace': ['trace.zip']}
    test_folders = (
        'test-approved-guest-features-py-test-approved-guest-features-chromium',
        'test-approved-mobile-menu-keyboard-focus-py-test-approved-mobile-menu-keyboard-focus-chromium',
        'test-approved-guest-opens-docs-py-test-approved-guest-opens-docs-chromium',
    )
    for name in test_folders:
        folder = artifacts / name
        for kind, names in names_by_kind.items():
            for name in names:
                path = (folder / name).resolve()
                if path.is_relative_to(root) and path.is_file():
                    found.setdefault(kind, path)
                    break
    return found
