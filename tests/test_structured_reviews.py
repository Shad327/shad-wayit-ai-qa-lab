from fastapi.testclient import TestClient
from qa_pipeline.api import create_app


def test_structured_edit_approval_and_source_changes(tmp_path):
    source=tmp_path/'requirements.md'
    source.write_text('**AUTH-04** Public browsing needs no wallet.')
    db=tmp_path/'reviews.sqlite3'
    client=TestClient(create_app(source,db))
    url='/structured-reviews/AUTH-04'
    first=client.post(url+'/sample',json={'revision':0}).json()['review']
    assert first['mode']=='demo_data'
    assert first['draft']['scenarios'][0]['source_ids']==['AUTH-04']
    assert client.post(url+'/sample',json={'revision':0}).status_code==409
    assert client.post(url+'/approve',json={'revision':1}).json()['review']['approved']
    draft=first['draft'];draft['scenarios'][0]['steps'][0]['expected_result']='Public navigation is visible'
    changed=client.put(url,json={'revision':1,'draft':draft}).json()['review']
    assert changed['revision']==2 and not changed['approved']
    assert client.post(url+'/approve',json={'revision':1}).status_code==409
    bad=first['draft'];bad['scenarios'][0]['source_ids']=['FAKE-99']
    assert client.put(url,json={'revision':2,'draft':bad}).status_code==422
    source.write_text('**AUTH-04** Updated browsing rule.')
    assert client.get(url).json()['review']['evidence_stale']
    assert client.post(url+'/approve',json={'revision':2}).status_code==409
    refreshed=client.post(url+'/refresh-evidence',json={'revision':2}).json()['review']
    assert refreshed['revision']==3 and not refreshed['evidence_stale']
    assert refreshed['draft']['scenarios'][0]['steps'][0]['expected_result']=='Public navigation is visible'
    assert client.post(url+'/approve',json={'revision':3}).status_code==200
    restored=TestClient(create_app(source,db)).get(url).json()['review']
    assert restored['approved'] and restored['revision']==3


def test_empty_steps_rejected_and_legacy_review_preserved(tmp_path):
    source=tmp_path/'requirements.md';source.write_text('**AUTH-04** Browse freely.')
    client=TestClient(create_app(source,tmp_path/'reviews.sqlite3'))
    client.put('/reviews/AUTH-04',json={'revision':0,'scenario':'My earlier notes'})
    url='/structured-reviews/AUTH-04'
    body=client.post(url+'/sample',json={'revision':0}).json()['review']['draft']
    body['scenarios'][0]['steps']=[]
    assert client.put(url,json={'revision':1,'draft':body}).status_code==422
    assert client.get('/reviews/AUTH-04').json()['review']['scenario']=='My earlier notes'


def test_export_requires_current_approval_and_matches_digest(tmp_path):
    import hashlib
    import json
    source=tmp_path/'requirements.md';source.write_text('**AUTH-04** Browse freely.')
    client=TestClient(create_app(source,tmp_path/'reviews.sqlite3'))
    url='/structured-reviews/AUTH-04'
    first=client.post(url+'/sample',json={'revision':0}).json()['review']
    assert client.get(url+'/export?revision=1').status_code==409
    client.post(url+'/approve',json={'revision':1})
    exported=client.get(url+'/export?revision=1').json()
    canonical=json.dumps(exported['package'],sort_keys=True,separators=(',',':'),ensure_ascii=False)
    assert hashlib.sha256(canonical.encode()).hexdigest()==exported['sha256']
    assert exported['package']['model_called'] is False
    assert exported['package']['draft']==first['draft']
    assert client.get(url+'/export?revision=2').status_code==409
    source.write_text('**AUTH-04** Changed.')
    assert client.get(url+'/export?revision=1').status_code==409


def test_preview_gates_and_rejects_unsupported_edits(tmp_path):
    import ast
    source = tmp_path / 'requirements.md'
    source.write_text('**AUTH-04** Browse freely.')
    client = TestClient(create_app(source, tmp_path / 'reviews.sqlite3'))
    url = '/structured-reviews/AUTH-04'
    draft = client.post(url+'/sample', json={'revision':0}).json()['review']['draft']
    assert client.get(url+'/test-preview?revision=1').status_code == 409
    client.post(url+'/approve', json={'revision':1})
    preview = client.get(url+'/test-preview?revision=1').json()
    ast.parse(preview['code'])
    assert preview['executed'] is False
    assert preview['mode'] == 'template_generated'
    assert preview['package_sha256'] == client.get(url+'/export?revision=1').json()['sha256']
    assert client.get(url+'/test-preview?revision=2').status_code == 409
    draft['scenarios'][0]['steps'][1]['expected_result'] = 'Run arbitrary command'
    client.put(url, json={'revision':1, 'draft':draft})
    client.post(url+'/approve', json={'revision':2})
    assert client.get(url+'/test-preview?revision=2').status_code == 422
    source.write_text('**AUTH-04** Changed.')
    assert client.get(url+'/test-preview?revision=2').status_code == 409


def test_supported_navigation_extensions_and_evaluation(tmp_path):
    source = tmp_path/'requirements.md';source.write_text('**AUTH-04** Browse public pages.')
    client = TestClient(create_app(source, tmp_path/'reviews.sqlite3'))
    url = '/structured-reviews/AUTH-04'
    review = client.post(url+'/sample', json={'revision':0}).json()['review']
    for label in ['About Us','How It Works','Roadmap']:
        review['draft']['scenarios'][0]['steps'].append({'action':f'Select {label}','expected_result':f'{label} section is visible'})
    client.put(url, json={'revision':1,'draft':review['draft']})
    result = client.get(url+'/evaluation').json()
    assert result['revision'] == 2 and result['status'] == 'needs_human_review'
    client.post(url+'/approve', json={'revision':2})
    code = client.get(url+'/test-preview?revision=2').json()['code']
    assert "name='Roadmap'" in code and 'Building the future of music' in code
    review['draft']['scenarios'][0]['steps'][-1]['expected_result'] = 'Receive tokens'
    client.put(url, json={'revision':2,'draft':review['draft']})
    client.post(url+'/approve', json={'revision':3})
    assert client.get(url+'/test-preview?revision=3').status_code == 422
