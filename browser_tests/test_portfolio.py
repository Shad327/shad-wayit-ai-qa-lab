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
    page.get_by_text("Earlier paragraph review", exact=True).click()
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
    page.get_by_text("Earlier paragraph review", exact=True).click()
    expect(scenario).to_have_value("Browser check: guest navigation is available without a wallet.")
    expect(page.get_by_role("status")).to_contain_text("Version 1 approved")
    scenario.fill("Revised browser check: also inspect the keyboard navigation.")
    expect(page.get_by_role("button", name="View template", exact=True)).to_be_disabled()
    page.get_by_role("button", name="Save changes", exact=True).click()
    expect(page.get_by_role("status")).to_contain_text("Version 2 saved · awaiting review")
    expect(approve).to_be_enabled()


def test_attach_real_evidence_to_sample_and_reload(page, isolated_review_api):
    def proxy(route):
        path = route.request.url.split("/qa-api/", 1)[1]
        route.fulfill(response=route.fetch(url=f"{isolated_review_api}/{path}"))
    page.route("**/qa-api/**", proxy)
    page.goto("http://localhost:5173/")
    page.get_by_role("button", name="03Review").click()
    page.get_by_text("Earlier paragraph review", exact=True).click()
    page.get_by_role("button", name="Attach evidence and save sample").click()
    source = page.locator("summary").filter(has_text="Saved source: AUTH-04")
    expect(source).to_be_visible()
    source.click()
    expect(page.get_by_role("blockquote")).to_contain_text("AUTH-04")
    page.get_by_role("button", name="Approve saved version").click()
    expect(page.get_by_role("status")).to_contain_text("Version 1 approved")
    page.reload()
    page.get_by_role("button", name="03Review").click()
    page.get_by_text("Earlier paragraph review", exact=True).click()
    expect(source).to_be_visible()
    expect(page.get_by_role("status")).to_contain_text("Version 1 approved")
