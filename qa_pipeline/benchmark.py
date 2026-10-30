"""Versioned fixture benchmark for deterministic guardrails, not model accuracy."""
from copy import deepcopy
from .evaluation import evaluate


def run_benchmark():
    packet={'status':'ready_for_model','prompt_version':'fixture-v1','evidence':{'results':[{'id':'AUTH-04','text':'Public browsing without wallet.'}]}}
    base={'scenarios':[{'title':'Guest','preconditions':[], 'steps':[{'action':'Open page','expected_result':'Public content'}], 'source_ids':['AUTH-04']}], 'questions':[]}
    cases=[]
    for name in ['valid_structure','unknown_citation','empty_steps','duplicate','unsupported_semantic_claim','open_question']:
        draft=deepcopy(base)
        expected='needs_human_review'
        if name=='unknown_citation':draft['scenarios'][0]['source_ids']=['INVENTED'];expected='blocked'
        if name=='empty_steps':draft['scenarios'][0]['steps']=[];expected='blocked'
        if name=='duplicate':draft['scenarios'].append(deepcopy(draft['scenarios'][0]));expected='blocked'
        if name=='unsupported_semantic_claim':draft['scenarios'][0]['steps'][0]['expected_result']='Receive a guaranteed million-dollar reward'
        if name=='open_question':draft['questions']=['Which flows are in scope?']
        result=evaluate(draft,packet)
        cases.append({'name':name,'expected':expected,'actual':result['status'],'matched':result['status']==expected})
    return {'version':'guardrails-v1','mode':'synthetic_fixtures','model_called':False,
            'matched':sum(c['matched'] for c in cases),'total':len(cases),'cases':cases,
            'limitation':'Matching fixture expectations is not model accuracy. The invented semantic claim intentionally requires human review; these checks cannot detect every hallucination.'}


if __name__=='__main__':
    import json
    print(json.dumps(run_benchmark(),indent=2))
