from pathlib import Path


def test_downloaded_evidence_matches_displayed_evidence():
    root=Path(__file__).resolve().parents[1]
    for name in ['result.json','workflow.json','benchmark.json']:
        assert (root/'data/demo'/name).read_bytes()==(root/'public/demo'/name).read_bytes()
