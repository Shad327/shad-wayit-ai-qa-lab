from uuid import uuid4
import re

from playwright.sync_api import expect
from qa_pipeline.generated_jobs import GeneratedRunManager


def test_history_accessible_directly_from_results(page, isolated_review_api, tmp_path):
    manager = GeneratedRunManager(tmp_path, tmp_path/'generated-runs.sqlite3', lambda: {})
    identifier = str(uuid4())
    with manager.connection() as db:
        db.execute('INSERT INTO runs (id,state,plan_hash,approved_at,finished_at) VALUES (?,?,?,?,?)',
                   (identifier, 'interrupted', 'a'*64, '2026-09-13T12:00:00Z', '2026-09-13T12:00:01Z'))
    def proxy(route):
        path = route.request.url.split('/qa-api/', 1)[1]
        route.fulfill(response=route.fetch(url=f'{isolated_review_api}/{path}'))
    page.route('**/qa-api/**', proxy)
    page.goto('http://localhost:5173/#results')
    history = page.get_by_role('region', name='Generated test history')
    expect(history).to_contain_text(identifier)
    history.get_by_role('button', name=re.compile('^interrupted')).click()
    expect(history.get_by_role('article', name='Selected generated run')).to_contain_text('interrupted')
    expect(history).to_contain_text('No browser artifacts available for this run.')
    page.reload()
    expect(history).to_contain_text(identifier)
