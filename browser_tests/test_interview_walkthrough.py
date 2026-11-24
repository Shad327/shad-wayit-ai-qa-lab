"""Recorded local interview workflow; explicitly runs public NoiseLabz navigation."""
import os
import pytest
from playwright.sync_api import expect


@pytest.fixture
def browser_context_args(browser_context_args):
    if os.environ.get('QA_RECORD_WALKTHROUGH') == '1':
        return {**browser_context_args,
                'viewport': {'width': 1920, 'height': 1080},
                'record_video_size': {'width': 1920, 'height': 1080}}
    return browser_context_args


@pytest.mark.skipif(os.environ.get('QA_TEST_GENERATED_RUN') != '1', reason='Explicit live public-site run only')
def test_interview_walkthrough(page, isolated_review_api):
    recording = os.environ.get('QA_RECORD_WALKTHROUGH') == '1'
    def pause_at(locator, seconds=5):
        if recording:
            locator.scroll_into_view_if_needed()
            page.wait_for_timeout(seconds * 1000)
    def proxy(route):
        path = route.request.url.split('/qa-api/', 1)[1]
        route.fulfill(response=route.fetch(url=f'{isolated_review_api}/{path}'))
    page.route('**/qa-api/**', proxy)
    page.set_viewport_size({'width':1920,'height':1080} if recording else {'width':1440,'height':1000})
    page.goto('http://localhost:5173/?lab')
    if recording:
        page.add_style_tag(content='body { zoom: 1.25; } html { scroll-behavior: auto; }')
    pause_at(page.get_by_role('heading', level=1), 3)
    page.get_by_role('button', name='03Review').click()
    editor = page.get_by_role('region', name='Structured scenario review')
    editor.get_by_role('button', name='Create structured sample').click()
    for section in ['About Us', 'How It Works', 'Roadmap']:
        editor.get_by_label('Add supported navigation').select_option(label=section)
    editor.get_by_role('button', name='Save structured changes').click()
    pause_at(editor.get_by_label('Test title'), 6)
    evaluation = editor.get_by_role('region', name='Scenario evaluation')
    expect(evaluation).to_contain_text('Structure and citation membership: passed')
    expect(evaluation).to_contain_text('Semantic support and requirement coverage: review')
    pause_at(evaluation, 7)
    editor.get_by_role('button', name='Approve structured version').click()
    pause_at(editor.get_by_role('button', name='Preview Python test'), 3)
    editor.get_by_role('button', name='Preview Python test').click()
    preview = editor.get_by_role('region', name='Generated test preview')
    expect(preview.locator('code')).to_contain_text('Building the future of music')
    pause_at(preview, 8)
    editor.get_by_role('checkbox', name='I reviewed this generated code and approve its public UI check.').check()
    pause_at(editor.get_by_role('button', name='Run approved generated test'), 4)
    editor.get_by_role('button', name='Run approved generated test').click()
    expect(editor.get_by_text('Run status:', exact=False)).to_contain_text('passed', timeout=180000)
    pause_at(editor.get_by_text('Run status:', exact=False), 4)
    page.get_by_role('button', name='05Results').click()
    history = page.get_by_role('region', name='Generated test history')
    history.get_by_role('button', name=__import__('re').compile('^passed')).first.click()
    expect(history.get_by_role('img')).to_be_visible()
    expect(history.get_by_role('img')).to_have_js_property('complete', True)
    assert history.get_by_role('img').evaluate('image => image.naturalWidth') > 0
    pause_at(history.get_by_role('img'), 7)
