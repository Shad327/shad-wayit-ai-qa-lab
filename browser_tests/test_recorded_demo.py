import pytest
from playwright.sync_api import expect


@pytest.mark.parametrize('width', [390,1440])
def test_recorded_showcase_without_backend(page, width):
    page.set_viewport_size({'width':width,'height':844})
    page.route('**/qa-api/**', lambda route: route.abort())
    page.goto('http://localhost:5173/demo')
    expect(page.get_by_role('heading', name='From approved scenario to a real browser run')).to_be_visible()
    video = page.get_by_label('Recorded local QA workflow')
    expect(video).to_be_visible()
    page.get_by_role('button', name='Evidence', exact=True).click()
    image = page.get_by_role('img', name='Final Roadmap section after the generated navigation test')
    expect(image).to_be_visible()
    expect(image).to_have_js_property('complete', True)
    assert image.evaluate('i => i.naturalWidth') > 0
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    page.get_by_role('button', name='Limits', exact=True).click()
    expect(page.get_by_text('This hosted page displays recorded evidence.', exact=False)).to_be_visible()
