"""Explicit opt-in browser test: starts the fixed public NoiseLabz suite."""
import os
import re
import pytest
from playwright.sync_api import expect


@pytest.mark.parametrize("state,color", [("passed", "rgb(134, 239, 172)"), ("failed", "rgb(252, 165, 165)")])
def test_run_status_colors(page, state, color):
    page.route("**/qa-api/runs/plan", lambda route: route.fulfill(json={
        "hash": "test-plan", "target": "https://example.com", "scope": "Mocked display check",
        "timeout_seconds": 60, "case_ids": []}))
    page.route("**/qa-api/runs/latest", lambda route: route.fulfill(json={"run": {
        "id": "display-test", "state": state, "approved_at": "2026-09-18T12:00:00Z",
        "finished_at": "2026-09-18T12:01:00Z", "note": None}}))
    page.goto("http://localhost:5173/?lab")
    page.get_by_role("button", name="05Results").click()
    status = page.get_by_role("article", name="Run approved NoiseLabz suite").get_by_role("status")
    expect(status).to_contain_text(state)
    expect(status.locator("strong")).to_have_css("color", color)


@pytest.mark.skipif(os.getenv("QA_TEST_RUN_WORKFLOW") != "1", reason="Set QA_TEST_RUN_WORKFLOW=1 to launch a real NoiseLabz run")
def test_approve_run_and_receive_real_results(page):
    page.goto("http://localhost:5173/?lab#results")
    runner = page.get_by_role("article", name="Run approved NoiseLabz suite")
    approve = runner.get_by_role("checkbox")
    expect(approve).to_be_visible()
    start = runner.get_by_role("button", name="Run approved suite", exact=True)
    expect(start).to_be_disabled()
    approve.check()
    expect(start).to_be_enabled()
    start.click()
    expect(runner.get_by_role("status")).to_contain_text(re.compile(r"queued|running|passed|failed"), timeout=15000)
    expect(runner.get_by_role("status")).to_contain_text(re.compile(r"Run status: (passed|failed)"), timeout=190000)
    expect(page.get_by_label("Latest NoiseLabz run")).to_contain_text("7")
    case = page.locator("details.test-case").filter(has_text="KEY-02")
    case.locator("summary").click()
    expect(case.get_by_role("img")).to_be_visible()
