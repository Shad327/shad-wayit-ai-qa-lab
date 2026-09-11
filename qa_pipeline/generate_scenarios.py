"""Run one paid generation after explicitly configuring local environment variables."""
import argparse
import json
from pathlib import Path

from .generation import prepare_generation
from .model import GenerationError, generate
from .retrieval import load_document


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--query", required=True)
    args = parser.parse_args()
    try:
        packet = prepare_generation(load_document(args.source), args.query)
        print(json.dumps(generate(packet), indent=2))
    except (GenerationError, OSError, ValueError) as exc:
        parser.exit(1, f"Generation stopped: {exc}\n")


if __name__ == "__main__":
    main()
