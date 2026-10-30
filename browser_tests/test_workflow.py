from playwright.sync_api import expect


def test_fixture_workflow_requires_human_review(page, isolated_review_api):
    def proxy(route):
        path = route.request.url.split('/qa-api/', 1)[1]
        route.fulfill(response=route.fetch(url=f'{isolated_review_api}/{path}'))
    page.route('**/qa-api/**', proxy)
    page.goto('http://localhost:5173/')
    page.get_by_role('button', name='03Review').click()
    workflow = page.get_by_role('region', name='Coordinated QA workflow')
    workflow.get_by_role('button', name='Run guardrail benchmark').click()
    expect(workflow.get_by_role('region', name='Guardrail benchmark')).to_contain_text('6/6 fixture expectations matched')
    workflow.get_by_role('button', name='Run fixture workflow · no AI calls').click()
    expect(workflow).to_contain_text('Model requests attempted: 0')
    expect(workflow).to_contain_text('Human approval: pending')
    workflow.get_by_role('button', name='Replace saved guest draft with this workflow draft').click()
    editor = page.get_by_role('region', name='Structured scenario review')
    editor.get_by_role('button', name='Reload structured review (replaces unsaved edits)').click()
    expect(editor.get_by_label('Test title')).to_have_value('Guest can use public navigation')
    expect(editor.get_by_role('status')).to_contain_text('awaiting approval')
    expect(editor.get_by_role('button', name='Preview Python test')).to_be_disabled()
