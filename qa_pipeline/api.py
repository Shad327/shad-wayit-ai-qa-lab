"""Local read-only retrieval API. Start with uvicorn qa_pipeline.api:app.

The source path is configured by the operator, never supplied by an API caller.
Bind to loopback; authentication and deployment are separate later milestones.
"""

import os
import sqlite3
from typing import Literal
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .retrieval import load_document, retrieve
from .generation import prepare_generation
from .reviews import ReviewStore
from .results import browser_reports


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


def create_app(source_path: Path = None, review_path: Path = None) -> FastAPI:
    source = source_path or Path(os.environ.get(
        "QA_REQUIREMENTS_PATH",
        str(Path(__file__).resolve().parents[1] / "outputs" / "requirements.md"),
    ))
    api = FastAPI(title="Shad QA Evidence API", version="0.1.0")
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
        return {"review": reviews.read(identifier)}

    @api.put("/reviews/{identifier}")
    def save_review(identifier: Literal["AUTH-04", "keyboard"], request: ReviewEdit):
        return {"review": reviews.update(identifier, request.revision, request.scenario)}

    @api.post("/reviews/{identifier}/approve")
    def approve_review(identifier: Literal["AUTH-04", "keyboard"], request: ReviewRevision):
        return {"review": reviews.update(identifier, request.revision, approve=True)}

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

    @api.get("/browser-results")
    def results():
        return browser_reports(Path(__file__).resolve().parents[1] / "outputs")

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
