"""Narrow public landing-page smoke check; not full AUTH-04 coverage."""
import re
import pytest
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


@pytest.mark.parametrize("label,fragment,heading", [
    ("About Us", "about", "About NOiSE"),
    ("How It Works", "hiw", "From sound to on-chain legacy"),
    ("Roadmap", "roadmap", "Building the future of music"),
])
def test_desktop_navigation(page, label, fragment, heading):
    page.goto("https://www.noiselabz.com/", wait_until="domcontentloaded")
    page.get_by_role("link", name=label, exact=True).first.click()
    expect(page).to_have_url(re.compile(f"#{fragment}$"))
    expect(page.get_by_role("heading", name=heading, exact=True)).to_be_in_viewport()


def test_features_link_can_be_activated_with_keyboard(page):
    page.goto("https://www.noiselabz.com/", wait_until="domcontentloaded")
    features = page.get_by_role("link", name="Features", exact=True).first
    # Use actual Tab traversal, not programmatic focus, to test reachability.
    for _ in range(20):
        page.keyboard.press("Tab")
        if features.evaluate("element => element === document.activeElement"):
            break
    expect(features).to_be_focused()
    page.keyboard.press("Enter")
    expect(page).to_have_url(re.compile(r"#features$"))


def test_mobile_menu_opens_and_selects_features(page):
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto("https://www.noiselabz.com/", wait_until="domcontentloaded")
    menu = page.locator(".hamburger")
    expect(menu).to_be_visible()
    menu.click()
    page.locator('a[href="#features"]:visible').first.click()
    expect(page).to_have_url(re.compile(r"#features$"))
    expect(page.get_by_role("heading", name="Everything you need to create & earn", exact=True)).to_be_in_viewport()


def test_mobile_menu_is_keyboard_reachable(page):
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto("https://www.noiselabz.com/", wait_until="domcontentloaded")
    menu = page.locator(".hamburger")
    expect(menu).to_be_visible()
    for _ in range(20):
        page.keyboard.press("Tab")
        if menu.evaluate("element => element === document.activeElement"):
            break
    expect(menu).to_be_focused()
