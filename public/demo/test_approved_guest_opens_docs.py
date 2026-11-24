import re
from playwright.sync_api import expect


def test_approved_guest_opens_docs(page):
    response = page.goto("https://www.noiselabz.com/", wait_until="domcontentloaded")
    assert response and response.ok
    link = page.get_by_role("link", name="Open Docs", exact=True)
    link.click()
    expect(page).to_have_url("https://www.noiselabz.com/docs/")
    expect(page.get_by_role("heading", level=1)).to_contain_text(re.compile("litepaper", re.I))
    expect(page.get_by_role("link", name="Read Litepaper", exact=True)).to_be_visible()
    expect(page.get_by_role("link", name="Open Protocol", exact=True)).to_be_visible()
