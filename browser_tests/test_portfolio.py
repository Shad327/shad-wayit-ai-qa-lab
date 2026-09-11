from playwright.sync_api import expect


def test_review_survives_reload_and_edit_clears_approval(page, isolated_review_api):
    def proxy(route):
        path = route.request.url.split("/qa-api/", 1)[1]
        response = route.fetch(url=f"{isolated_review_api}/{path}")
        route.fulfill(response=response)
    # Only reroute to an isolated real backend. No API responses are mocked.
    page.route("**/qa-api/**", proxy)
    page.goto("http://localhost:5173/")
    page.get_by_role("button", name="03Review").click()
    scenario = page.get_by_label("Scenario", exact=True)
    expect(scenario).to_be_enabled()
    scenario.fill("Browser check: guest navigation is available without a wallet.")
    page.get_by_role("button", name="Save changes", exact=True).click()
    approve = page.get_by_role("button", name="Approve saved version", exact=True)
    expect(approve).to_be_enabled()
    approve.click()
    expect(page.get_by_role("status")).to_contain_text("Version 1 approved")
    page.reload()
    page.get_by_role("button", name="03Review").click()
    expect(scenario).to_have_value("Browser check: guest navigation is available without a wallet.")
    expect(page.get_by_role("status")).to_contain_text("Version 1 approved")
    scenario.fill("Revised browser check: also inspect the keyboard navigation.")
    expect(page.get_by_role("button", name="View template", exact=True)).to_be_disabled()
    page.get_by_role("button", name="Save changes", exact=True).click()
    expect(page.get_by_role("status")).to_contain_text("Version 2 saved · awaiting review")
    expect(approve).to_be_enabled()
