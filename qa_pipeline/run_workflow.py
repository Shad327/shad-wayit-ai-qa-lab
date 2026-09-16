"""Run a fixture workflow, or explicitly authorize at most two model requests."""
import argparse
import os
from pathlib import Path
from .workflow import run_workflow


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live',action='store_true')
    parser.add_argument('--confirm-live',action='store_true')
    args=parser.parse_args()
    if args.live and not args.confirm_live:
        parser.error('Live mode requires --confirm-live; no calls made')
    if args.live and (os.getenv('QA_ENABLE_LIVE_MODEL')!='1' or not os.getenv('OPENAI_API_KEY') or not os.getenv('QA_MODEL')):
        parser.error('Live model is not configured; no calls made')
    root=Path(__file__).resolve().parents[1]
    import fcntl
    output=root/'outputs';output.mkdir(exist_ok=True)
    with (output/'model-generation.lock').open('w') as lock:
        try: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError: parser.error('Another model command is active; no calls made')
        result=run_workflow(Path(os.environ.get('QA_REQUIREMENTS_PATH',output/'requirements.md')),output/'workflows',live=args.live)
    print(f"Workflow {result['id']}: {result['status']} ({result['mode']}); requests attempted: {result['model_calls']}")
    print('Open the local workflow panel and load this ID to inspect or import it.')
    raise SystemExit(1 if result['status']=='failed' else 0)


if __name__=='__main__': main()
