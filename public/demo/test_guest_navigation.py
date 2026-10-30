"""Template-generated narrow public navigation check; not full AUTH-04 coverage."""
import re
from playwright.sync_api import expect


def test_approved_guest_features(page):
    page.set_viewport_size({"width": 1280, "height": 800})
    response = page.goto("https://www.noiselabz.com/", wait_until="domcontentloaded")
    assert response and response.ok
    expect(page).to_have_title(re.compile("noise", re.I))
    features = page.get_by_role("link", name="Features", exact=True).first
    expect(features).to_be_visible()
    features.click()
    expect(page).to_have_url(re.compile(r"#features$"))
    expect(page.get_by_role("heading", name="Everything you need to create & earn", exact=True)).to_be_in_viewport()
    page.get_by_role("link", name='About Us', exact=True).first.click()
    expect(page).to_have_url(re.compile('#about$'))
    expect(page.get_by_role("heading", name='About NOiSE', exact=True)).to_be_in_viewport()
    page.get_by_role("link", name='How It Works', exact=True).first.click()
    expect(page).to_have_url(re.compile('#hiw$'))
    expect(page.get_by_role("heading", name='From sound to on-chain legacy', exact=True)).to_be_in_viewport()
    page.get_by_role("link", name='Roadmap', exact=True).first.click()
    expect(page).to_have_url(re.compile('#roadmap$'))
    expect(page.get_by_role("heading", name='Building the future of music', exact=True)).to_be_in_viewport()
