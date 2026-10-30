"""Single-worker local execution of the fixed, reviewed NoiseLabz suite only."""
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import signal
import sqlite3
import subprocess
import sys
import threading
from uuid import UUID

from fastapi import HTTPException

CASES = ["NAV-01", "NAV-02", "NAV-03", "NAV-04", "KEY-01", "MOB-01", "KEY-02"]


def now():
    return datetime.now(timezone.utc).isoformat()


class RunManager:
    def __init__(self, root: Path, database: Path):
        self.root = root.resolve()
        self.database = database
        self.stopping = threading.Event()
        self.process_lock = threading.Lock()
        self.process = None
        self.worker = None

    def shutdown(self):
        self.stopping.set()
        with self.process_lock:
            if self.process is not None and self.process.poll() is None:
                try:
                    os.killpg(self.process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
        if self.worker:
            self.worker.join(timeout=5)

    @contextmanager
    def connection(self):
        self.database.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(self.database, timeout=5)
        db.row_factory = sqlite3.Row
        try:
            db.execute("CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, state TEXT NOT NULL, plan_hash TEXT NOT NULL, approved_at TEXT NOT NULL, started_at TEXT, finished_at TEXT, exit_code INTEGER, report TEXT, note TEXT)")
            db.commit()
            with db:
                yield db
        finally:
            db.close()

    def plan(self):
        suite = self.root / "browser_tests" / "test_noiselabz.py"
        # Include fixtures/config that affect the executed suite in approval identity.
        contents = b""
        for path in [suite, self.root / "browser_tests" / "conftest.py", self.root / "pyproject.toml"]:
            contents += str(path.relative_to(self.root)).encode() + b"\0" + path.read_bytes()
        return {"hash": hashlib.sha256(contents).hexdigest(), "case_ids": CASES,
                "target": "https://www.noiselabz.com/", "mode": "hand_written_suite",
                "scope": "Seven public desktop/mobile navigation and keyboard checks. No sign-in, wallet, or transaction actions.",
                "timeout_seconds": 180}

    def recover(self):
        with self.connection() as db:
            db.execute("UPDATE runs SET state = 'interrupted', finished_at = ?, note = 'API restarted before completion was recorded; inspect artifacts before rerunning.' WHERE state IN ('queued', 'running')", (now(),))

    def get(self, identifier):
        with self.connection() as db:
            row = db.execute("SELECT * FROM runs WHERE id = ?", (identifier,)).fetchone()
            if row is None:
                raise HTTPException(404, "Run not found")
            return dict(row)

    def latest(self):
        with self.connection() as db:
            row = db.execute("SELECT * FROM runs ORDER BY approved_at DESC LIMIT 1").fetchone()
            return dict(row) if row else None

    def enqueue(self, identifier: UUID, plan_hash: str, approved: bool, dispatch=True):
        identifier = str(identifier)
        if not approved:
            raise HTTPException(422, "Review and approve the fixed suite before running it")
        if plan_hash != self.plan()["hash"]:
            raise HTTPException(409, "The suite changed. Reload and review the current plan.")
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute("SELECT * FROM runs WHERE id = ?", (identifier,)).fetchone()
            if existing:
                if existing["plan_hash"] != plan_hash:
                    raise HTTPException(409, "Request ID belongs to a different plan")
                return dict(existing)
            if db.execute("SELECT id FROM runs WHERE state IN ('queued', 'running')").fetchone():
                raise HTTPException(409, "A run is already active. Wait for it to finish.")
            db.execute("INSERT INTO runs (id,state,plan_hash,approved_at) VALUES (?,'queued',?,?)", (identifier, plan_hash, now()))
        if dispatch:
            self.worker = threading.Thread(target=self.execute, args=(identifier,), daemon=True)
            self.worker.start()
        return self.get(identifier)

    report_prefix = "browser-noiselabz"

    def browser_output(self, artifact):
        return artifact

    def test_arguments(self, artifact):
        return ["browser_tests/test_noiselabz.py"]

    def execute(self, identifier):
        process = None
        state, code, note = "error", None, "Runner could not start; check local browser installation."
        report = f"{self.report_prefix}-{identifier}.xml"
        artifact = self.root / "outputs" / report.removesuffix(".xml")
        try:
            if self.get(identifier)["plan_hash"] != self.plan()["hash"]:
                raise RuntimeError("Suite changed after approval")
            with self.connection() as db:
                db.execute("UPDATE runs SET state='running', started_at=? WHERE id=?", (now(), identifier))
            artifact.mkdir(parents=True, exist_ok=False)
            command = [sys.executable, "-m", "pytest", *self.test_arguments(artifact), "-q",
                       "--browser", "chromium", "--screenshot", "on", "--tracing", "on",
                       "--output", str(self.browser_output(artifact)), "--junitxml", str(artifact.with_suffix(".xml"))]
            env = {k: os.environ[k] for k in ("HOME", "PATH", "TMPDIR", "LANG", "PLAYWRIGHT_BROWSERS_PATH") if k in os.environ}
            with artifact.with_suffix(".log").open("w") as log:
                with self.process_lock:
                    if self.stopping.is_set():
                        raise RuntimeError("Runner is shutting down")
                    process = subprocess.Popen(command, cwd=self.root, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                    self.process = process
                code = process.wait(timeout=180)
            state = "passed" if code == 0 else "failed" if code == 1 else "error"
            note = "Inspect report assertions; a failure can reflect product, test, or environment behavior."
        except subprocess.TimeoutExpired:
            state, note = "timed_out", "Run exceeded 180 seconds and was stopped."
        except (OSError, RuntimeError, HTTPException):
            pass
        finally:
            if process is not None and process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
            if self.stopping.is_set():
                state, note = "interrupted", "API stopped during execution; inspect partial artifacts before rerunning."
            with self.connection() as db:
                db.execute("UPDATE runs SET state=?, finished_at=?, exit_code=?, report=?, note=? WHERE id=?",
                           (state, now(), code, report if artifact.with_suffix(".xml").is_file() else None, note, identifier))
