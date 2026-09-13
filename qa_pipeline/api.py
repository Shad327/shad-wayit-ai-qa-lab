"""Local read-only retrieval API. Start with uvicorn qa_pipeline.api:app.

The source path is configured by the operator, never supplied by an API caller.
Bind to loopback; authentication and deployment are separate later milestones.
"""

import os
import sqlite3
from contextlib import asynccontextmanager
from uuid import UUID
from typing import Literal
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .retrieval import load_document, retrieve
from .generation import prepare_generation
from .reviews import ReviewStore
from .results import browser_reports
from .jobs import RunManager


class RunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: UUID
    plan_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    approved: bool = Field(strict=True)


class ReviewRevision(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    revision: int = Field(ge=0)


class ReviewEdit(ReviewRevision):
    scenario: str = Field(min_length=1, max_length=8000)

    @field_validator("scenario")
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError("Scenario cannot be blank")
        return value.strip()


class SearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    query: str = Field(min_length=1, max_length=2000)
    limit: int = Field(default=3, ge=1, le=10)

    @field_validator("query")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Query cannot be blank")
        return value.strip()


def create_app(source_path: Path = None, review_path: Path = None, run_manager=None) -> FastAPI:
    source = source_path or Path(os.environ.get(
        "QA_REQUIREMENTS_PATH",
        str(Path(__file__).resolve().parents[1] / "outputs" / "requirements.md"),
    ))
    root = Path(__file__).resolve().parents[1]
    runs = run_manager or RunManager(root, (review_path.parent if review_path else root / "outputs") / "runs.sqlite3")

    @asynccontextmanager
    async def lifespan(api):
        runs.recover()
        try:
            yield
        finally:
            runs.shutdown()

    api = FastAPI(title="Shad QA Evidence API", version="0.2.0", lifespan=lifespan)
    api.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "testserver"])
    reviews = ReviewStore(review_path or Path(__file__).resolve().parents[1] / "outputs" / "reviews.sqlite3")

    @api.middleware("http")
    async def local_writes(request, call_next):
        # Block browser cross-origin writes; this is still a local single-user service.
        from starlette.responses import JSONResponse
        if request.method in {"PUT", "POST", "DELETE", "PATCH"}:
            origin = request.headers.get("origin")
            if origin and origin not in {"http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8000", "http://127.0.0.1:8000"}:
                return JSONResponse({"detail": "Origin is not allowed"}, status_code=403)
        try:
            return await call_next(request)
        except (sqlite3.Error, OSError):
            return JSONResponse({"detail": "Review storage is unavailable. Your changes were not confirmed."}, status_code=503)

    @api.get("/reviews/{identifier}")
    def get_review(identifier: Literal["AUTH-04", "keyboard"]):
        review = reviews.read(identifier)
        if review and review["evidence"]:
            passages = read_source()
            current_hash = passages[0].document_sha256 if passages else None
            review["evidence_stale"] = any(p["document_sha256"] != current_hash for p in review["evidence"])
            if review["evidence_stale"]:
                review["approved"] = False
        return {"review": review}

    @api.put("/reviews/{identifier}")
    def save_review(identifier: Literal["AUTH-04", "keyboard"], request: ReviewEdit):
        reviews.update(identifier, request.revision, request.scenario)
        return get_review(identifier)

    @api.post("/reviews/{identifier}/approve")
    def approve_review(identifier: Literal["AUTH-04", "keyboard"], request: ReviewRevision):
        review = reviews.read(identifier)
        passages = read_source() if review and review["evidence"] else []
        return {"review": reviews.update(identifier, request.revision, approve=True,
                                        current_hash=passages[0].document_sha256 if passages else None)}

    @api.post("/reviews/{identifier}/from-evidence")
    def sample_from_evidence(identifier: Literal["AUTH-04", "keyboard"], request: ReviewRevision):
        query = "AUTH-04" if identifier == "AUTH-04" else "keyboard focus"
        packet = prepare_generation(read_source(), query, 1)
        evidence = packet["evidence"]["results"]
        if not evidence:
            raise HTTPException(409, "No matching evidence; no sample draft created")
        sample = ("Open the public landing page without connecting a wallet. Use Features navigation and verify the destination section is visible. This checks public navigation only, not every AUTH-04 activity."
                  if identifier == "AUTH-04" else
                  "At a 390 × 844 viewport, open the public landing page and press Tab to reach the visible menu trigger. Verify it receives keyboard focus. Check visible focus styling separately.")
        previous = reviews.read(identifier)
        # Preserve human edits when attaching or refreshing evidence.
        text = previous["scenario"] if previous else sample
        return {"review": reviews.update(identifier, request.revision, scenario=text, evidence=evidence)}

    def read_source():
        try:
            return load_document(source)
        except (OSError, UnicodeError, ValueError):
            raise HTTPException(503, "Requirements source is unavailable or invalid") from None

    @api.get("/health")
    def health():
        passages = read_source()
        return {"status": "ready", "method": "lexical_baseline", "passages": len(passages),
                "model_calls": False}

    @api.get("/runs/plan")
    def execution_plan():
        return runs.plan()

    @api.get("/runs/latest")
    def latest_run():
        return {"run": runs.latest()}

    @api.get("/runs/{identifier}")
    def run_status(identifier: UUID):
        return {"run": runs.get(str(identifier))}

    @api.post("/runs", status_code=202)
    def start_run(request: RunRequest):
        return {"run": runs.enqueue(request.request_id, request.plan_hash, request.approved)}

    @api.get("/browser-results")
    def results():
        return browser_reports(Path(__file__).resolve().parents[1] / "outputs")

    @api.get("/browser-artifacts/{run}/{case}/{filename}")
    def screenshot(run: str, case: str, filename: str):
        root = (Path(__file__).resolve().parents[1] / "outputs").resolve()
        target = (root / run / case / filename).resolve()
        if (not run.startswith("browser-") or not case.startswith("browser-tests-test-noiselabz-py-")
                or filename not in {"test-failed-1.png", "test-finished-1.png"}
                or not target.is_relative_to(root) or not target.is_file()):
            raise HTTPException(404, "Screenshot not found")
        return FileResponse(target, media_type="image/png")

    @api.post("/retrieve")
    def search(request: SearchRequest):
        # Reread for each request so edits never silently return stale evidence.
        return retrieve(read_source(), request.query, request.limit)

    @api.post("/generation/prepare")
    def prepare(request: SearchRequest):
        # Preview only: no provider connection, generated output, or paid calls.
        return prepare_generation(read_source(), request.query, request.limit)

    return api


app = create_app()
