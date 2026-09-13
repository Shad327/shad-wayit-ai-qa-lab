"""Exercise the local interview demo against its saved real NoiseLabz report."""
from playwright.sync_api import expect


def test_demo_shows_case_evidence_and_refresh(page):
    page.goto("http://localhost:5173/#results")
    demo = page.get_by_role("region", name="NoiseLabz quality demo")
    expect(demo).to_be_visible()
    expect(demo.get_by_label("Latest NoiseLabz run")).to_be_visible()
    case = demo.locator("details.test-case").filter(has_text="KEY-02")
    case.locator("summary").click()
    expect(case).to_contain_text("test_mobile_menu_is_keyboard_reachable")
    screenshot = case.get_by_role("img")
    expect(screenshot).to_be_visible()
    expect(screenshot).to_have_js_property("complete", True)
    assert screenshot.evaluate("img => img.naturalWidth") > 0
    demo.get_by_role("button", name="Refresh results", exact=True).click()
    expect(demo.get_by_role("button", name="Refresh results", exact=True)).to_be_enabled()
    expect(demo.get_by_text("KEY-02", exact=True)).to_be_visible()
