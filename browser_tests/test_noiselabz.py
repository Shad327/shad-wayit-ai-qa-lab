"""Narrow public landing-page smoke check; not full AUTH-04 coverage."""
import re
from playwright.sync_api import expect


def test_guest_can_open_features_without_signing_in(page):
    response = page.goto("https://www.noiselabz.com/", wait_until="domcontentloaded")
    assert response and response.ok, "Landing page should return a successful HTTP response"
    expect(page).to_have_title(re.compile("noise", re.I))
    # Desktop header is the first Features link; footer and mobile menu repeat it.
    features = page.get_by_role("link", name="Features", exact=True).first
    expect(features).to_be_visible()
    features.click()
    expect(page).to_have_url(re.compile(r"#features$"))
    expect(page.get_by_role("heading", name="Everything you need to create & earn", exact=True)).to_be_in_viewport()
