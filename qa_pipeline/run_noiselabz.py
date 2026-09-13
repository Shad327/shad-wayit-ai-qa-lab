"""Run the fixed public UI suite and retain a unique report for the portfolio."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--headed", action="store_true", help="Show Chromium during the run")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    run = "browser-noiselabz-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    artifact = root / "outputs" / run
    command = [sys.executable, "-m", "pytest", "browser_tests/test_noiselabz.py", "-v",
               "--browser", "chromium", "--screenshot", "on", "--tracing", "on",
               "--output", str(artifact), "--junitxml", str(artifact.with_suffix(".xml"))]
    if args.headed:
        command.append("--headed")
    result = subprocess.run(command, cwd=root)
    print(f"Report: {artifact.with_suffix('.xml')}")
    print("Open Results in the local portfolio and select Refresh results.")
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
