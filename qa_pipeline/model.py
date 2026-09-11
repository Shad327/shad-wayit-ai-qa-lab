"""Single-call OpenAI adapter. Live use is explicitly enabled by the operator."""
import json
import os

import httpx

from .generation import validate_draft


class GenerationError(RuntimeError):
    """Safe error message that excludes credentials and provider response bodies."""


def generate(packet: dict, *, client=None) -> dict:
    if packet["status"] != "ready_for_model":
        raise GenerationError("No evidence: model call skipped")
    if os.getenv("QA_ENABLE_LIVE_MODEL") != "1":
        raise GenerationError("Live model calls are disabled")
    key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("QA_MODEL", "").strip()
    if not key or not model:
        raise GenerationError("Configure OPENAI_API_KEY and QA_MODEL locally")
    evidence = json.dumps(packet["evidence"], ensure_ascii=False)
    if len(evidence.encode("utf-8")) > 32_000:
        raise GenerationError("Evidence exceeds the 32 KB input limit")
    payload = {"model": model, "instructions": packet["instructions"], "input": evidence,
        "store": False, "max_output_tokens": 3000,
        "text": {"format": {"type": "json_schema", "name": "qa_scenarios",
                            "strict": True, "schema": packet["response_schema"]}}}
    owned = client is None
    client = client or httpx.Client(timeout=60, follow_redirects=False)
    try:
        response = client.post("https://api.openai.com/v1/responses",
            headers={"Authorization": f"Bearer {key}"}, json=payload)
        response.raise_for_status()
        body = response.json()
        if body.get("status") != "completed":
            raise GenerationError("Model response did not complete; no draft accepted")
        texts = []
        for item in body.get("output", []):
            if item.get("type") != "message":
                continue
            for content in item.get("content", []):
                if content.get("type") == "refusal":
                    raise GenerationError("Model declined the request")
                if content.get("type") == "output_text":
                    texts.append(content["text"])
        if len(texts) != 1:
            raise GenerationError("Expected one structured model response")
        result = validate_draft(texts[0], packet)
        result.update(model_called=True, model=model, usage=body.get("usage"))
        return result
    except httpx.HTTPError:
        raise GenerationError("Model request failed; no automatic retry was made") from None
    except (ValueError, KeyError, TypeError, AttributeError):
        raise GenerationError("Model output failed validation; no draft accepted") from None
    finally:
        if owned:
            client.close()
