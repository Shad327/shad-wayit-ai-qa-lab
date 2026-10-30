"""Run with python -m qa_pipeline --source FILE --query TEXT."""

import argparse
import json
from pathlib import Path

from .retrieval import load_document, retrieve


def main() -> None:
    parser = argparse.ArgumentParser(description="Retrieve source-backed QA requirements without API calls")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--query", required=True)
    parser.add_argument("--limit", type=int, default=3)
    args = parser.parse_args()
    try:
        result = retrieve(load_document(args.source), args.query, args.limit)
    except (OSError, UnicodeError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
