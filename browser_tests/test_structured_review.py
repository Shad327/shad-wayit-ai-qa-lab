import json
import os
from pathlib import Path

from playwright.sync_api import expect


def test_mixed_scenarios_keep_manual_work_visible(page, isolated_review_api):
    from copy import deepcopy
    url = isolated_review_api + '/structured-reviews/AUTH-04'
    draft = page.request.post(url + '/sample', data={'revision': 0}).json()['review']['draft']
    manual = deepcopy(draft['scenarios'][0])
    manual.update(title='Listen without a wallet', steps=[{'action': 'Play a song', 'expected_result': 'Audio is audible'}])
    draft['scenarios'].insert(0, manual)
    assert page.request.put(url, data={'revision': 1, 'draft': draft}).ok
    assert page.request.post(url + '/approve', data={'revision': 2}).ok
    def proxy(route):
        path = route.request.url.split('/qa-api/', 1)[1]
        route.fulfill(response=route.fetch(url=f'{isolated_review_api}/{path}'))
    page.route('**/qa-api/**', proxy)
    page.goto('http://localhost:5173/?lab')
    page.get_by_role('button', name='03Review').click()
    editor = page.get_by_role('region', name='Structured scenario review')
    expect(editor.get_by_text('Manual review · automation not supported', exact=True)).to_be_visible()
    editor.get_by_role('button', name='Preview Python test').click()
    scope = editor.get_by_label('Automation scope')
    expect(scope).to_contain_text('Scenario 1: Listen without a wallet')
    expect(scope).to_contain_text('Manual only · not executed')
    expect(scope).to_contain_text('Scenario 2: Guest can use public navigation')
    expect(editor.get_by_role('article', name='Test scenario 1: Listen without a wallet')).to_be_visible()
    assert page.request.get(url).json()['review']['draft'] == draft


def test_structured_sample_edit_save_approve_reload(page,isolated_review_api):
    def proxy(route):
        path=route.request.url.split('/qa-api/',1)[1]
        route.fulfill(response=route.fetch(url=f'{isolated_review_api}/{path}'))
    page.route('**/qa-api/**',proxy)
    page.goto('http://localhost:5173/?lab')
    page.get_by_role('button',name='03Review').click()
    editor=page.get_by_role('region',name='Structured scenario review')
    editor.get_by_role('button',name='Create structured sample').click()
    expect(editor.get_by_label('Test title')).to_have_value('Guest can use public navigation')
    editor.get_by_label('Expected result 1',exact=True).fill('Visible public content without a wallet')
    editor.get_by_role('button',name='Add step',exact=True).click()
    editor.get_by_label('Action 3',exact=True).fill('Return to the top of the page')
    editor.get_by_label('Expected result 3',exact=True).fill('Public navigation remains available')
    editor.get_by_role('button',name='Save structured changes').click()
    editor.get_by_role('button',name='Approve structured version').click()
    expect(editor.get_by_role('status')).to_contain_text('Structured version 2 approved')
    with page.expect_download() as download_event:
        editor.get_by_role('button',name='Download approved package').click()
    download = download_event.value
    assert download.suggested_filename == 'approved-AUTH-04-v2.json'
    package = json.loads(Path(download.path()).read_text())['package']
    assert package['revision'] == 2
    assert package['model_called'] is False
    assert package['draft']['scenarios'][0]['steps'][2]['action'] == 'Return to the top of the page'
    page.reload()
    page.get_by_role('button',name='03Review').click()
    expect(editor.get_by_label('Action 3',exact=True)).to_have_value('Return to the top of the page')
    expect(editor.get_by_role('status')).to_contain_text('Structured version 2 approved')
    editor.get_by_label('Test title').fill('Updated review')
    expect(editor.get_by_role('button',name='Download approved package')).to_be_disabled()
    expect(editor.get_by_role('button',name='Approve structured version')).to_be_disabled()
    editor.get_by_role('button',name='Save structured changes').click()
    expect(editor.get_by_role('status')).to_contain_text('Structured version 3 awaiting approval')


def test_approved_template_preview(page, isolated_review_api):
    def proxy(route):
        path = route.request.url.split('/qa-api/', 1)[1]
        route.fulfill(response=route.fetch(url=f'{isolated_review_api}/{path}'))
    page.route('**/qa-api/**', proxy)
    page.goto('http://localhost:5173/?lab')
    page.get_by_role('button', name='03Review').click()
    editor = page.get_by_role('region', name='Structured scenario review')
    editor.get_by_role('button', name='Create structured sample').click()
    button = editor.get_by_role('button', name='Preview Python test')
    expect(button).to_be_disabled()
    editor.get_by_role('button', name='Approve structured version').click()
    button.click()
    preview = editor.get_by_role('region', name='Generated test preview')
    expect(preview).to_contain_text('def test_approved_guest_features(page):')
    with page.expect_download() as event:
        editor.get_by_role('button', name='Download Python test').click()
    assert event.value.suggested_filename == 'test_approved_guest_features.py'
    code = Path(event.value.path()).read_text()
    assert code == preview.locator('code').inner_text()
    compile(code, 'downloaded_test.py', 'exec')
    if os.environ.get('QA_TEST_GENERATED_RUN') == '1':
        editor.get_by_role('checkbox', name='I reviewed this generated code and approve its public UI check.').check()
        editor.get_by_role('button', name='Run approved generated test').click()
        expect(editor.get_by_text('Run status:', exact=False)).to_contain_text('passed', timeout=180000)
        expect(editor.get_by_role('link', name='Download generated-run report (if available)')).to_be_visible()
        screenshot = editor.get_by_role('img', name='Final browser state from this generated NoiseLabz test')
        expect(screenshot).to_be_visible()
        expect(screenshot).to_have_js_property('complete', True)
        assert screenshot.evaluate('image => image.naturalWidth') > 0
        with page.expect_download() as trace_event:
            editor.get_by_role('link', name='Download Playwright trace').click()
        import zipfile
        assert zipfile.is_zipfile(trace_event.value.path())

    editor.get_by_label('Expected result 2', exact=True).fill('Something else')
    expect(preview).to_have_count(0)
    editor.get_by_role('button', name='Save structured changes').click()
    editor.get_by_role('button', name='Approve structured version').click()
    button.click()
    alert = editor.get_by_role('alert')
    expect(alert).to_contain_text('Python preview blocked')
    expect(alert).to_contain_text('Test scenario 1: Guest can use public navigation')
    expect(alert).to_contain_text('Step 2')
    expect(alert).to_be_focused()
    expect(alert).to_be_in_viewport()
