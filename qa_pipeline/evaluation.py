"""Deterministic QA checks, not a model judge or a semantic-accuracy score."""
import json
from .generation import validate_draft


def evaluate(draft, packet):
    checks = []
    try:
        validated = validate_draft(json.dumps(draft), packet)
        checks.append({'name':'Structure and citation membership', 'status':'passed', 'detail':'Required fields are valid; cited IDs exist in retrieved evidence.'})
    except ValueError:
        return {'status':'blocked', 'checks':[{'name':'Structure and citation membership','status':'failed','detail':'Invalid fields, missing evidence, or citations outside the retrieved packet.'}], 'model_called':False}
    scenarios = validated['draft']['scenarios']
    signatures = [json.dumps({'steps':s['steps'],'preconditions':s['preconditions']},sort_keys=True) for s in scenarios]
    duplicate = len(signatures) != len(set(signatures))
    checks.append({'name':'Duplicate scenarios','status':'failed' if duplicate else 'passed','detail':'Duplicate step/precondition sequences found.' if duplicate else 'No identical step/precondition sequences.'})
    cited = {source for s in scenarios for source in s['source_ids']}
    retrieved = {p['id'] for p in validated['evidence']}
    missing = sorted(retrieved-cited)
    checks.append({'name':'Retrieved passages cited','status':'review' if missing else 'passed','detail':f'Uncited retrieved passages: {", ".join(missing)}' if missing else 'All retrieved passage IDs are cited. This does not measure requirement coverage.'})
    questions = validated['draft']['questions']
    checks.append({'name':'Open questions','status':'review' if questions else 'passed','detail':f'{len(questions)} unresolved questions retained for review.' if questions else 'No questions recorded; missing knowledge may still exist.'})
    checks.append({'name':'Semantic support and requirement coverage','status':'review','detail':'A human must check whether evidence supports each expected result and whether important cases are missing. Citation membership is not proof.'})
    return {'status':'blocked' if duplicate else 'needs_human_review','checks':checks,'model_called':False}
