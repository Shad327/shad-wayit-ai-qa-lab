"""Local read-only retrieval API. Start with uvicorn qa_pipeline.api:app.

The source path is configured by the operator, never supplied by an API caller.
Bind to loopback; authentication and deployment are separate later milestones.
"""

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .retrieval import load_document, retrieve


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


def create_app(source_path: Path = None) -> FastAPI:
    source = source_path or Path(os.environ.get(
        "QA_REQUIREMENTS_PATH",
        str(Path(__file__).resolve().parents[1] / "outputs" / "requirements.md"),
    ))
    api = FastAPI(title="Shad QA Evidence API", version="0.1.0")
    api.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "testserver"])

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

    @api.post("/retrieve")
    def search(request: SearchRequest):
        # Reread for each request so edits never silently return stale evidence.
        return retrieve(read_source(), request.query, request.limit)

    return api


app = create_app()
