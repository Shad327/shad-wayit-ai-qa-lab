"""Exercise the local interview demo against its saved real NoiseLabz report."""
from playwright.sync_api import expect


def test_demo_shows_case_evidence_and_refresh(page, isolated_review_api):
    def proxy(route):
        path = route.request.url.split('/qa-api/', 1)[1]
        route.fulfill(response=route.fetch(url=f'{isolated_review_api}/{path}'))
    page.route('**/qa-api/**', proxy)
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

    finding = demo.get_by_role('article', name='Keyboard accessibility finding')
    image = finding.get_by_role('img', name='KEY-02 failure screenshot: mobile menu keyboard test')
    expect(image).to_be_visible()
    expect(image).to_have_js_property('complete', True)
    assert image.evaluate('img => img.naturalWidth') > 0
    with page.expect_download() as report:
        finding.get_by_role('link', name='Download KEY-02 run report').click()
    assert report.value.suggested_filename.endswith('.xml')
