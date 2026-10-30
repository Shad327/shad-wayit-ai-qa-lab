from copy import deepcopy
import pytest
from qa_pipeline.evaluation import evaluate


def example():
    draft = {'scenarios':[{'title':'Guest','preconditions':[], 'steps':[{'action':'Open page','expected_result':'Public content'}], 'source_ids':['AUTH-04']}], 'questions':[]}
    packet = {'status':'ready_for_model','prompt_version':'v1','evidence':{'results':[{'id':'AUTH-04','text':'Public browsing'}]}}
    return draft, packet


def test_valid_citation_does_not_prove_semantics():
    draft, packet = example()
    draft['scenarios'][0]['steps'][0]['expected_result'] = 'Invented reward of one million dollars'
    result = evaluate(draft, packet)
    assert result['status'] == 'needs_human_review'
    assert result['checks'][-1]['status'] == 'review'
    assert result['model_called'] is False


@pytest.mark.parametrize('mutation', ['unknown_citation','empty_steps','duplicate','no_evidence'])
def test_negative_benchmark(mutation):
    draft, packet = example()
    if mutation == 'unknown_citation': draft['scenarios'][0]['source_ids'] = ['INVENTED']
    if mutation == 'empty_steps': draft['scenarios'][0]['steps'] = []
    if mutation == 'duplicate': draft['scenarios'].append(deepcopy(draft['scenarios'][0]))
    if mutation == 'no_evidence': packet['status'] = 'no_evidence'
    assert evaluate(draft, packet)['status'] == 'blocked'
