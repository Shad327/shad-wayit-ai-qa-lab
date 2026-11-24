"""Check local results rendering with synthetic, isolated report fixtures.

No NoiseLabz execution occurs. Artifact responses are intercepted by the test;
these cases check the report parser and frontend, not backend file-serving routes.
"""
from pathlib import Path
from shutil import copyfile

from playwright.sync_api import expect

from qa_pipeline.results import browser_reports


def serve_demo_reports(page, api_url, directory):
    """Keep results independent of the owner's outputs/ and retain the local API."""
    def proxy(route):
        path = route.request.url.split('/qa-api/', 1)[1]
        if path == 'browser-results':
            route.fulfill(json=browser_reports(directory))
        elif path.startswith('browser-artifacts/'):
            relative = Path(path.removeprefix('browser-artifacts/'))
            target = (directory / relative).resolve()
            assert target.is_relative_to(directory.resolve())
            route.fulfill(path=str(target), content_type='image/png')
        elif path.startswith('browser-reports/'):
            target = directory / Path(path).name
            route.fulfill(
                path=str(target), content_type='application/xml',
                headers={'Content-Disposition': f'attachment; filename="{target.name}"'},
            )
        else:
            route.fulfill(response=route.fetch(url=f'{api_url}/{path}'))

    page.route('**/qa-api/**', proxy)


def test_demo_shows_case_evidence_and_refresh(page, isolated_review_api, tmp_path):
    # Synthetic failed case exercises the finding UI; it is not a real run result.
    report_xml = '''<testsuite name="synthetic-ui-fixture" timestamp="2026-10-31T12:00:00">
      <testcase classname="browser_tests.test_noiselabz"
                name="test_mobile_menu_is_keyboard_reachable[chromium]">
        <failure message="Synthetic failure for results-display testing"/>
      </testcase>
    </testsuite>'''
    (tmp_path / 'browser-synthetic.xml').write_text(report_xml, encoding='utf-8')
    image_folder = (
        tmp_path / 'browser-synthetic'
        / 'browser-tests-test-noiselabz-py-test-mobile-menu-is-keyboard-reachable-chromium'
    )
    image_folder.mkdir(parents=True)
    # Reuse a valid public image only to verify image loading, not failure semantics.
    source_image = Path(__file__).resolve().parents[1] / 'public/demo/generated-result.png'
    copyfile(source_image, image_folder / 'test-failed-1.png')
    serve_demo_reports(page, isolated_review_api, tmp_path)
    page.goto("http://localhost:5173/?lab#results")
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
    assert Path(report.value.path()).read_text(encoding='utf-8') == report_xml


def test_demo_shows_empty_results_without_saved_reports(page, isolated_review_api, tmp_path):
    serve_demo_reports(page, isolated_review_api, tmp_path)
    page.goto('http://localhost:5173/?lab#results')
    demo = page.get_by_role('region', name='NoiseLabz quality demo')
    expect(demo.get_by_text(
        'No NoiseLabz report yet. Run the suite below to create one.', exact=True,
    )).to_be_visible()
    expect(demo.get_by_label('Latest NoiseLabz run')).to_have_count(0)
    expect(demo.get_by_role('article', name='Keyboard accessibility finding')).to_have_count(0)
