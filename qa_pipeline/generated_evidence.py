"""Allowlisted artifacts for the single supported generated browser test."""
from pathlib import Path
from uuid import UUID


def evidence_files(output_root: Path, identifier: UUID):
    root = output_root.resolve()
    folder = root / f'generated-web-{identifier}' / 'artifacts' / 'test-approved-guest-features-py-test-approved-guest-features-chromium'
    found = {}
    for kind, names in {'screenshot': ['test-failed-1.png', 'test-finished-1.png'], 'trace': ['trace.zip']}.items():
        for name in names:
            path = (folder / name).resolve()
            if path.is_relative_to(root) and path.is_file():
                found[kind] = path
                break
    return found
