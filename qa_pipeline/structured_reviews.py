"""Persist structured sample drafts using the model-output validation contract."""
import json
import hashlib

from fastapi import HTTPException
from .reviews import ReviewStore
from .generation import validate_draft


class StructuredReviews(ReviewStore):
    def export(self, identifier, revision, current_hash):
        review = self.record(identifier, current_hash)
        if review is None:
            raise HTTPException(404, "Review not found")
        if review["revision"] != revision or not review["approved"]:
            raise HTTPException(409, "Export requires the current approved version and unchanged source evidence")
        payload = {"format_version":1,"requirement":identifier,"revision":review["revision"],
                   "mode":review["mode"],"model_called":review["provenance"]["model_called"],"provenance":review["provenance"],"prompt_version":review["prompt_version"],
                   "approved_at":review["approved_at"],"approval_scope":"local single-user review; identity not verified",
                   "draft":review["draft"],"evidence":review["evidence"],
                   "execution_status":"not_generated_or_executed",
                   "note":"Origin is recorded in provenance; later human edits retain that origin. Open questions are retained. This package does not authorize arbitrary code execution."}
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return {"package":payload,"sha256":hashlib.sha256(canonical.encode()).hexdigest()}

    # Reuse transaction handling; store these records under separate, fixed IDs.
    def record(self, identifier, current_hash):
        raw = self.read("structured:" + identifier)
        if raw is None:
            return None
        data = json.loads(raw.pop("scenario"))
        provenance = data.get("provenance", {"model_called":False,"origin":"hand_written_sample"})
        stale = any(p["document_sha256"] != current_hash for p in raw["evidence"])
        return {**raw, "draft": data["draft"], "prompt_version": data["prompt_version"],
                "provenance":provenance, "mode":"model_generated" if provenance["model_called"] else "demo_data",
                "evidence_stale": stale, "approved": raw["approved"] and not stale}

    def sample(self, identifier, packet, revision):
        if packet["status"] != "ready_for_model":
            raise HTTPException(409, "No evidence found; no sample created")
        current = self.read("structured:" + identifier)
        if current:
            raise HTTPException(409, "A structured draft already exists. Reload it to preserve your edits.")
        guest = identifier == "AUTH-04"
        draft = {"scenarios": [{"title": "Guest can use public navigation" if guest else "Mobile menu is keyboard reachable",
            "preconditions": ["Fresh browser context; no wallet connected" if guest else "Mobile viewport 390 × 844; fresh browser context"],
            "steps": [{"action": "Open the public landing page", "expected_result": "Public page content is visible"},
                      {"action": "Select Features" if guest else "Press Tab to reach the menu trigger",
                       "expected_result": "Features section is visible" if guest else "Menu trigger receives keyboard focus"}],
            "source_ids": [packet["evidence"]["results"][0]["id"]]}],
            "questions": ["Which additional off-chain flows need coverage?" if guest else "What visible focus style is required?"]}
        self.save(identifier, revision, draft, packet)

    def save(self, identifier, revision, draft, packet, provenance=None):
        try:
            checked = validate_draft(json.dumps(draft), packet)
        except ValueError:
            raise HTTPException(422, "Invalid scenario structure or source reference") from None
        if provenance is None:
            previous = self.read("structured:" + identifier)
            provenance = json.loads(previous["scenario"]).get("provenance") if previous else None
        provenance = provenance or {"model_called":False,"origin":"hand_written_sample"}
        payload = json.dumps({"draft": checked["draft"], "prompt_version": packet["prompt_version"], "provenance":provenance}, sort_keys=True)
        return self.update("structured:" + identifier, revision, scenario=payload, evidence=checked["evidence"])

    def packet(self, identifier):
        saved = self.read("structured:" + identifier)
        if saved is None:
            raise HTTPException(404, "Create a sample draft first")
        return {"status":"ready_for_model", "prompt_version":json.loads(saved["scenario"])["prompt_version"],
                "evidence":{"results":saved["evidence"]}}
