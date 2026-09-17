"""Employer-facing showcase acceptance without the private Python backend."""
import math

import pytest
from playwright.sync_api import expect


@pytest.mark.parametrize("width", [320, 390, 1440])
def test_showcase_media_downloads_and_sections(page, width, tmp_path):
    page.set_viewport_size({"width": width, "height": 900})
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.route("**/qa-api/**", lambda route: route.abort())
    page.goto("http://localhost:5173/demo")
    video = page.get_by_label("Recorded local QA workflow")
    expect(video).to_have_js_property("readyState", 4, timeout=15000)
    duration = video.evaluate("video => video.duration")
    assert math.isfinite(duration) and duration > 0
    video.evaluate("video => { video.muted = true; return video.play(); }")
    page.wait_for_function("document.querySelector('video').currentTime > 0")
    video.evaluate("video => video.pause()")

    for section in ["Walkthrough", "Evidence", "Architecture", "Limits"]:
        page.get_by_role("button", name=section, exact=True).click()
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), section
        page.screenshot(path=str(tmp_path / f"showcase-{width}-{section}.png"), full_page=True)

    for path in ["result.json", "workflow.json", "benchmark.json", "test_guest_navigation.py"]:
        response = page.request.get(f"http://localhost:5173/demo/{path}")
        assert response.ok, path
        assert len(response.body()) > 0
        assert "text/html" not in response.headers.get("content-type", ""), path
    assert not errors
