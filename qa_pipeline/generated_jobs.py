"""Run only the currently approved, supported generated template."""
import hashlib
import json

from fastapi import HTTPException
from .jobs import RunManager
from .test_generation import generate_preview


class GeneratedRunManager(RunManager):
    report_prefix = 'generated-web'

    def __init__(self, root, database, export_current):
        super().__init__(root, database)
        self.export_current = export_current

    def history(self):
        with self.connection() as db:
            return [dict(row) for row in db.execute("SELECT * FROM runs ORDER BY approved_at DESC, id DESC LIMIT 10").fetchall()]

    def plan(self):
        exported = self.export_current()
        preview = generate_preview(exported)
        identity = json.dumps(preview, sort_keys=True) + '\nrunner-v1'
        return {**preview, 'hash': hashlib.sha256(identity.encode()).hexdigest(),
                'scope': 'One template-generated public guest navigation test with optional About Us, How It Works, and Roadmap steps. No wallet or transaction actions.',
                'target': 'https://www.noiselabz.com/', 'timeout_seconds': 180}

    def browser_output(self, artifact):
        return artifact / "artifacts"

    def test_arguments(self, artifact):
        plan = self.plan()
        identifier = artifact.name.removeprefix(self.report_prefix + '-')
        if self.get(identifier)['plan_hash'] != plan['hash']:
            raise HTTPException(409, 'Approved scenario changed before launch')
        test = artifact / 'test_approved_guest_features.py'
        test.write_text(plan['code'])
        (artifact / 'manifest.json').write_text(json.dumps(plan, indent=2))
        config = artifact / 'pytest.ini'
        config.write_text('[pytest]\n')
        return ['-c', str(config), '--confcutdir', str(artifact), str(test)]
