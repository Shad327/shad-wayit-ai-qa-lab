"""Local, single-operator review storage. No identity verification or execution."""
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException


class ReviewStore:
    def __init__(self, path: Path):
        self.path = path

    @contextmanager
    def connection(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        try:
            db.execute("CREATE TABLE IF NOT EXISTS reviews (id TEXT PRIMARY KEY, scenario TEXT NOT NULL, revision INTEGER NOT NULL, approved_revision INTEGER, updated_at TEXT NOT NULL, approved_at TEXT)")
            db.commit()
            with db:
                yield db
        finally:
            db.close()

    def read(self, identifier):
        with self.connection() as db:
            row = db.execute("SELECT * FROM reviews WHERE id = ?", (identifier,)).fetchone()
            return self.render(row) if row else None

    @staticmethod
    def render(row):
        return {**dict(row), "mode": "demo_data", "approved": row["approved_revision"] == row["revision"]}

    def update(self, identifier, revision, scenario=None, approve=False):
        now = datetime.now(timezone.utc).isoformat()
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM reviews WHERE id = ?", (identifier,)).fetchone()
            if (row["revision"] if row else 0) != revision:
                raise HTTPException(409, "This scenario changed elsewhere. Reload the saved review before continuing.")
            if approve:
                if row is None:
                    raise HTTPException(409, "Save the scenario before approving it")
                db.execute("UPDATE reviews SET approved_revision = revision, approved_at = ?, updated_at = ? WHERE id = ?", (now, now, identifier))
            elif row is None:
                db.execute("INSERT INTO reviews VALUES (?, ?, 1, NULL, ?, NULL)", (identifier, scenario, now))
            elif scenario != row["scenario"]:
                db.execute("UPDATE reviews SET scenario = ?, revision = revision + 1, approved_revision = NULL, approved_at = NULL, updated_at = ? WHERE id = ?", (scenario, now, identifier))
            return self.render(db.execute("SELECT * FROM reviews WHERE id = ?", (identifier,)).fetchone())
