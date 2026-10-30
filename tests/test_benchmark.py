from qa_pipeline.benchmark import run_benchmark


def test_fixture_results_do_not_claim_semantic_detection():
    result=run_benchmark()
    assert result['matched']==result['total']==6
    assert not result['model_called']
    semantic=next(c for c in result['cases'] if c['name']=='unsupported_semantic_claim')
    assert semantic['actual']=='needs_human_review'
