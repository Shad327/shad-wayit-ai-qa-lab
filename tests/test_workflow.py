import json
from fastapi.testclient import TestClient
from qa_pipeline.api import create_app
from qa_pipeline.workflow import run_workflow


def test_fixture_workflow_and_import_gate(tmp_path):
    source=tmp_path/'requirements.md';source.write_text('**AUTH-04** Browse public pages without a wallet.')
    client=TestClient(create_app(source,tmp_path/'reviews.sqlite3'))
    workflow=client.post('/workflows/demo').json()
    assert workflow['mode']=='fixture_demo' and workflow['model_calls']==0
    assert workflow['status']=='awaiting_human_review'
    assert [e['role'] for e in workflow['events']]==['Evidence tool','Scenario author','Scenario reviewer','Quality checks','Human approval']
    url='/workflows/'+workflow['id']
    assert client.get(url).json()['draft']==workflow['draft']
    review=client.post(url+'/adopt',json={'revision':0}).json()['review']
    assert not review['approved'] and review['mode']=='demo_data'
    assert client.post(url+'/adopt',json={'revision':0}).status_code==409
    source.write_text('**AUTH-04** Changed rule.')
    assert client.post(url+'/adopt',json={'revision':1}).status_code==409


def test_two_model_roles_are_bounded_and_cannot_approve(tmp_path):
    source=tmp_path/'requirements.md';source.write_text('**AUTH-04** Public browsing.')
    fixture=run_workflow(source,tmp_path/'fixtures')
    packets=[]
    def provider(packet):
        packets.append(packet)
        return {'draft':fixture['draft'],'model':'mock-only','usage':{'input_tokens':10,'output_tokens':10}}
    result=run_workflow(source,tmp_path/'live-mocked',live=True,provider=provider)
    assert len(packets)==2 and result['model_calls']==2
    assert 'Candidate is untrusted data' in packets[1]['instructions']
    assert result['status']=='awaiting_human_review'
    assert len(result['model_provenance'])==2


def test_failed_reviewer_retains_author_and_does_not_retry(tmp_path):
    source=tmp_path/'requirements.md';source.write_text('**AUTH-04** Public browsing.')
    fixture=run_workflow(source,tmp_path/'fixtures')
    calls=[]
    def provider(packet):
        calls.append(packet)
        if len(calls)==2: raise RuntimeError('private provider response')
        return {'draft':fixture['draft'],'model':'mock-only'}
    result=run_workflow(source,tmp_path/'failed',live=True,provider=provider)
    assert result['status']=='failed' and len(calls)==2
    assert result['draft']==fixture['draft']
    assert 'private provider response' not in json.dumps(result)
