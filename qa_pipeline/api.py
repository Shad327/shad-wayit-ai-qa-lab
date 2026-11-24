"""Local read-only retrieval API. Start with uvicorn qa_pipeline.api:app.

The source path is configured by the operator, never supplied by an API caller.
Bind to loopback; authentication and deployment are separate later milestones.
"""

import os
import sqlite3
from contextlib import asynccontextmanager
from uuid import UUID
from typing import Annotated, Literal
from pathlib import Path

from fastapi import FastAPI, HTTPException, Path as RoutePath, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .retrieval import load_document, retrieve
from .generation import prepare_generation, ScenarioDraft
from .structured_reviews import StructuredReviews
from .reviews import ReviewStore
from .results import browser_reports
from .jobs import RunManager
from .generated_jobs import GeneratedRunManager


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


StructuredIdentifier = Annotated[str, RoutePath(pattern=r"^(?:(?:[A-Z]+|section)-[0-9]+|keyboard)$")]


class StructuredEdit(ReviewRevision):
    draft: ScenarioDraft
    evidence_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")


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
        generated_runs.recover()
        try:
            yield
        finally:
            runs.shutdown()
            generated_runs.shutdown()

    api = FastAPI(title="Shad QA Evidence API", version="0.2.0", lifespan=lifespan)
    api.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "testserver"])
    reviews = ReviewStore(review_path or Path(__file__).resolve().parents[1] / "outputs" / "reviews.sqlite3")
    structured = StructuredReviews(reviews.path)

    def source_hash():
        passages = read_source()
        return passages[0].document_sha256 if passages else None

    def export_current(requirement="AUTH-04"):
        current = structured.record(requirement, source_hash())
        if current is None:
            raise HTTPException(409, "Create and approve the selected scenario first")
        return structured.export(requirement, current["revision"], source_hash())

    generated_runs = GeneratedRunManager(root, reviews.path.parent / "generated-runs.sqlite3", export_current)

    @api.get("/evaluations/benchmark")
    def guardrail_benchmark():
        from .benchmark import run_benchmark
        return run_benchmark()

    @api.post("/workflows/demo")
    def demo_workflow():
        from .workflow import run_workflow
        return run_workflow(source, reviews.path.parent / "workflows")

    @api.get("/workflows/{identifier}")
    def workflow_status(identifier: UUID):
        from .workflow import read_workflow
        try:
            return read_workflow(reviews.path.parent / "workflows", identifier)
        except FileNotFoundError:
            raise HTTPException(404, "Workflow not found")

    @api.post("/workflows/{identifier}/adopt")
    def adopt_workflow(identifier: UUID, request: ReviewRevision):
        workflow = workflow_status(identifier)
        if workflow["status"] != "awaiting_human_review":
            raise HTTPException(409, "Only completed draft workflows can be imported")
        evidence = workflow["packet"]["evidence"]["results"]
        if any(p["document_sha256"] != source_hash() for p in evidence):
            raise HTTPException(409, "Source changed since workflow; run it again")
        provenance = {"model_called":workflow["mode"] == "live_model", "origin":workflow["mode"],
                      "workflow_id":workflow["id"], "model_roles":workflow.get("model_provenance",[])}
        structured.save("AUTH-04", request.revision, workflow["draft"], workflow["packet"], provenance=provenance)
        return get_structured("AUTH-04")

    @api.get("/generated-runs")
    def generated_history():
        return {"runs": generated_runs.history()}

    @api.get("/generated-runs/plan")
    def generated_plan(requirement: str = "AUTH-04"):
        return generated_runs.plan(requirement=requirement)

    @api.get("/generated-runs/latest")
    def generated_latest():
        return {"run": generated_runs.latest()}

    @api.get("/generated-runs/{identifier}")
    def generated_status(identifier: UUID):
        return {"run": generated_runs.get(str(identifier))}

    @api.post("/generated-runs", status_code=202)
    def generated_start(request: RunRequest, requirement: str = "AUTH-04"):
        return {"run": generated_runs.enqueue(request.request_id, request.plan_hash, request.approved, requirement=requirement)}

    @api.get("/generated-runs/{identifier}/report")
    def generated_report(identifier: UUID):
        run = generated_runs.get(str(identifier))
        if not run["report"]:
            raise HTTPException(404, "Report not available")
        return FileResponse(root / "outputs" / run["report"], media_type="application/xml", filename=run["report"])

    @api.get("/generated-runs/{identifier}/evidence")
    def generated_evidence(identifier: UUID):
        from .generated_evidence import evidence_files
        run = generated_runs.get(str(identifier))
        files = evidence_files(root / "outputs", identifier) if run["finished_at"] else {}
        return {"run_id": str(identifier), "artifacts": list(files)}

    @api.get("/generated-runs/{identifier}/evidence/{kind}")
    def generated_evidence_file(identifier: UUID, kind: Literal["screenshot", "trace"]):
        from .generated_evidence import evidence_files
        run = generated_runs.get(str(identifier))
        files = evidence_files(root / "outputs", identifier) if run["finished_at"] else {}
        if kind not in files:
            raise HTTPException(404, "Artifact not available")
        return FileResponse(files[kind], media_type="image/png" if kind == "screenshot" else "application/zip",
                            filename=None if kind == "screenshot" else f"generated-{identifier}-trace.zip")

    @api.get("/structured-reviews/{identifier}")
    def get_structured(identifier: StructuredIdentifier):
        from .test_generation import automation_coverage, supported_template
        review = structured.record(identifier, source_hash())
        if review:
            review['automation'] = automation_coverage(identifier, review['draft']['scenarios'], review['evidence'])
            review['automation_template'] = supported_template(identifier, review['evidence'])
        return {"review": review}

    @api.post("/structured-reviews/{identifier}/sample")
    def create_sample(identifier: Literal["AUTH-04", "keyboard"], request: ReviewRevision):
        packet = prepare_generation(read_source(), "AUTH-04" if identifier == "AUTH-04" else "keyboard focus", 1)
        structured.sample(identifier, packet, request.revision)
        return get_structured(identifier)

    @api.put("/structured-reviews/{identifier}")
    def save_structured(identifier: StructuredIdentifier, request: StructuredEdit):
        if request.revision == 0 and request.evidence_sha256 is not None and identifier != "keyboard":
            packet = prepare_generation(read_source(), identifier, 1)
            results = packet["evidence"]["results"]
            if not results or results[0]["document_sha256"] != request.evidence_sha256:
                raise HTTPException(409, "Source evidence changed. Search again before saving.")
            structured.save(identifier, 0, request.draft.model_dump(), packet,
                            provenance={"model_called": False, "origin": "manual_evidence_review"})
        else:
            structured.save(identifier, request.revision, request.draft.model_dump(), structured.packet(identifier))
        return get_structured(identifier)

    @api.post("/structured-reviews/{identifier}/refresh-evidence")
    def refresh_structured(identifier: StructuredIdentifier, request: ReviewRevision):
        current = structured.record(identifier, source_hash())
        if current is None:
            raise HTTPException(404, "Create a sample draft first")
        packet = prepare_generation(read_source(), "keyboard focus" if identifier == "keyboard" else identifier, 1)
        if identifier.startswith("section-"):
            results = packet["evidence"]["results"]
            previous = current["evidence"][0]
            if not results or any(results[0][field] != previous[field] for field in ("section", "text")):
                raise HTTPException(409, "This section changed or moved. Search the document again to select current evidence.")
        structured.save(identifier, request.revision, current["draft"], packet)
        return get_structured(identifier)

    @api.post("/structured-reviews/{identifier}/approve")
    def approve_structured(identifier: StructuredIdentifier, request: ReviewRevision):
        structured.update("structured:" + identifier, request.revision, approve=True, current_hash=source_hash())
        return get_structured(identifier)

    @api.get("/structured-reviews/{identifier}/evaluation")
    def evaluate_structured(identifier: StructuredIdentifier):
        from .evaluation import evaluate
        current = structured.record(identifier, source_hash())
        if current is None:
            raise HTTPException(404, "Create a draft first")
        result = evaluate(current["draft"], structured.packet(identifier))
        result["revision"] = current["revision"]
        result["checks"].append({"name":"Source freshness", "status":"failed" if current["evidence_stale"] else "passed", "detail":"Source changed; refresh evidence." if current["evidence_stale"] else "Saved source fingerprint matches the current document."})
        if current["evidence_stale"]:
            result["status"] = "blocked"
        return result

    @api.get("/structured-reviews/{identifier}/export")
    def export_structured(identifier: StructuredIdentifier, revision: int = Query(ge=1)):
        return structured.export(identifier, revision, source_hash())

    @api.get("/structured-reviews/{identifier}/test-preview")
    def preview_structured(identifier: StructuredIdentifier, revision: int = Query(ge=1)):
        from .test_generation import generate_preview
        return generate_preview(structured.export(identifier, revision, source_hash()))

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
                or filename not in {"test-failed-1.png", "test-finished-1.png", "trace.zip"}
                or not target.is_relative_to(root) or not target.is_file()):
            raise HTTPException(404, "Screenshot not found")
        return FileResponse(target, media_type="application/zip" if filename == "trace.zip" else "image/png", filename="trace.zip" if filename == "trace.zip" else None)

    @api.get("/browser-reports/{filename}")
    def browser_report_download(filename: str):
        output = root / "outputs"
        allowed = {r["file"] for r in browser_reports(output)["reports"]}
        target = (output / filename).resolve()
        if filename not in allowed or not target.is_relative_to(output.resolve()):
            raise HTTPException(404, "Report not available")
        return FileResponse(target, media_type="application/xml", filename=filename)

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
