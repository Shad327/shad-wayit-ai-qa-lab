"""Generate and save an unapproved draft. Explicit live-call opt-in is required."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from uuid import uuid4

from .generation import prepare_generation
from .model import generate
from .retrieval import load_document
from .structured_reviews import StructuredReviews


def generate_and_save(source, database, revision, recovery_directory, *, generator=generate):
    store = StructuredReviews(database)
    passages = load_document(source)
    fingerprint = passages[0].document_sha256 if passages else None
    current = store.record('AUTH-04', fingerprint)
    if (current['revision'] if current else 0) != revision:
        raise ValueError('Review changed. Reload its current revision before making a model call.')
    packet = prepare_generation(passages, 'AUTH-04', 1)
    result = generator(packet)
    # Preserve a paid response even if a concurrent review/source edit prevents saving.
    recovery_directory = Path(recovery_directory)
    recovery_directory.mkdir(parents=True, exist_ok=True)
    recovery = recovery_directory / f'draft-{uuid4()}.json'
    recovery.write_text(json.dumps(result, indent=2))
    latest = load_document(source)
    if not latest or latest[0].document_sha256 != fingerprint:
        raise ValueError(f'Source changed during generation. Draft retained for review at {recovery}')
    provenance = {'origin':'model', 'model_called':True, 'model':result['model'],
                  'usage':result.get('usage'), 'generated_at':datetime.now(timezone.utc).isoformat()}
    try:
        store.save('AUTH-04', revision, result['draft'], packet, provenance=provenance)
    except Exception as error:
        raise ValueError(f'Draft was not saved to the review. Recovery copy: {recovery}') from error
    return store.record('AUTH-04', fingerprint)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision', type=int, required=True, help='Current saved revision, or 0 for a new draft')
    parser.add_argument('--confirm-live', action='store_true', help='Authorize one potentially billable model request')
    args = parser.parse_args()
    if not args.confirm_live:
        parser.error('No call made. Add --confirm-live only after configuring and budgeting for model access.')
    import os
    import fcntl
    root = Path(__file__).resolve().parents[1]
    output = root / 'outputs'
    output.mkdir(exist_ok=True)
    # Avoid concurrent local CLI calls charging for the same review revision.
    with (output / 'model-generation.lock').open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.error('Another model-generation command is active; no call made.')
        review = generate_and_save(Path(os.environ.get('QA_REQUIREMENTS_PATH',output/'requirements.md')),
                                   output/'reviews.sqlite3', args.revision, output/'model-drafts')
    print(json.dumps({'revision':review['revision'], 'approved':review['approved'], 'mode':review['mode']}))
    print('Reload Review in the local website. Human approval is required; model output may not fit the constrained test compiler.')


if __name__ == '__main__':
    main()
