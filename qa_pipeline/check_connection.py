"""Check API connectivity; generation requires an explicit, bounded probe."""
import argparse
import json
import os
import re
from urllib.parse import quote

import httpx


def redact(value, key):
    text = str(value).replace(key, "[REDACTED]") if key else str(value)
    text = re.sub(r"sk-[A-Za-z0-9_-]+", "[REDACTED]", text)
    return text[:2000]


def check_connection(*, probe=False, client=None):
    key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("QA_MODEL", "").strip()
    if not key or not model:
        return {"status": "configuration_missing", "detail": "Set OPENAI_API_KEY and QA_MODEL in this terminal."}
    report = {"model": redact(model, key), "generation_requested": probe}
    owned = client is None
    client = client or httpx.Client(timeout=30, follow_redirects=False)
    try:
        headers = {"Authorization": f"Bearer {key}"}
        if probe:
            # No private documents, retries, fallback models, or workflow changes.
            response = client.post("https://api.openai.com/v1/responses", headers=headers,
                json={"model": model, "input": "Reply OK.", "store": False,
                      "max_output_tokens": 16})
        else:
            response = client.get("https://api.openai.com/v1/models/" + quote(model, safe=""), headers=headers)
        report["http_status"] = response.status_code
        for name in ("x-request-id", "openai-project", "openai-organization"):
            if response.headers.get(name):
                report[name] = redact(response.headers[name], key)
        try:
            body = response.json()
        except ValueError:
            body = {}
        if not isinstance(body, dict):
            body = {}
        if response.is_success:
            report["status"] = "generation_reachable" if probe else "lookup_only_passed"
            report["detail"] = ("Generation request accepted; the 16-token probe may be incomplete. Full workflow not tested."
                                if probe else "Model lookup passed. This does not verify generation access.")
            if probe:
                report["response_status"] = redact(body.get("status", "unknown"), key)
        else:
            report["status"] = "provider_rejected"
            error = body.get("error")
            if isinstance(error, dict):
                for field in ("code", "type", "param", "message"):
                    if isinstance(error.get(field), (str, int)):
                        report[field] = redact(error[field], key)
    except httpx.HTTPError:
        report.update(status="network_error", detail="Connection failed or timed out; no retry. A submitted probe may still be billed.")
    finally:
        if owned:
            client.close()
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", action="store_true", help="Authorize one paid request, capped at 16 output tokens; no private documents sent.")
    args = parser.parse_args()
    report = check_connection(probe=args.probe)
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["status"] in {"generation_reachable", "lookup_only_passed"} else 1)


if __name__ == "__main__":
    main()
