from copy import deepcopy
import pytest
from qa_pipeline.generate_review import generate_and_save
from qa_pipeline.structured_reviews import StructuredReviews


def reply(packet):
    return {'draft':{'scenarios':[{'title':'Generated guest scenario', 'preconditions':[],
        'steps':[{'action':'Browse','expected_result':'Public content'}], 'source_ids':['AUTH-04']}], 'questions':[]},
        'model':'simulated-model', 'model_called':True, 'usage':{'input_tokens':12,'output_tokens':20}}


def test_model_origin_persists_through_human_edits_and_export(tmp_path):
    source=tmp_path/'requirements.md';source.write_text('**AUTH-04** Public browsing.')
    db=tmp_path/'reviews.sqlite3'
    review=generate_and_save(source,db,0,tmp_path/'recovery',generator=reply)
    assert review['mode']=='model_generated' and not review['approved']
    assert review['provenance']['model']=='simulated-model'
    store=StructuredReviews(db)
    draft=deepcopy(review['draft']);draft['scenarios'][0]['title']='Human edited title'
    store.save('AUTH-04',1,draft,store.packet('AUTH-04'))
    updated=store.record('AUTH-04',review['evidence'][0]['document_sha256'])
    assert updated['provenance']==review['provenance']
    assert updated['revision']==2 and not updated['approved']
    fingerprint=review['evidence'][0]['document_sha256']
    store.update('structured:AUTH-04',2,approve=True,current_hash=fingerprint)
    package=store.export('AUTH-04',2,fingerprint)['package']
    assert package['model_called'] and package['provenance']['usage']['input_tokens']==12


def test_stale_revision_blocks_before_model(tmp_path):
    source=tmp_path/'requirements.md';source.write_text('**AUTH-04** Browse.')
    with pytest.raises(ValueError,match='Review changed'):
        generate_and_save(source,tmp_path/'db',4,tmp_path/'recovery',generator=lambda p:pytest.fail('No call'))


def test_source_change_keeps_recovery_without_accepting_draft(tmp_path):
    source=tmp_path/'requirements.md';source.write_text('**AUTH-04** Browse.')
    def changing(packet):
        source.write_text('**AUTH-04** Changed rule.')
        return reply(packet)
    with pytest.raises(ValueError,match='Source changed'):
        generate_and_save(source,tmp_path/'db',0,tmp_path/'recovery',generator=changing)
    assert len(list((tmp_path/'recovery').glob('*.json')))==1
    assert StructuredReviews(tmp_path/'db').read('structured:AUTH-04') is None
