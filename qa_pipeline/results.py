"""Read bounded local pytest reports; never execute submitted code."""
from pathlib import Path
from xml.etree import ElementTree


def browser_reports(directory: Path):
    reports = []
    for path in sorted(directory.glob("browser-*.xml"), key=lambda p: p.stat().st_mtime, reverse=True)[:5]:
        if path.stat().st_size > 2_000_000:
            continue
        try:
            root = ElementTree.fromstring(path.read_bytes())
            suite = root if root.tag == "testsuite" else root.find("testsuite")
            if suite is None:
                continue
            cases = []
            for case in suite.findall("testcase"):
                status = "passed"
                if case.find("failure") is not None or case.find("error") is not None:
                    status = "failed"
                elif case.find("skipped") is not None:
                    status = "skipped"
                cases.append({"name": case.get("name", "Unnamed test"), "status": status})
            reports.append({"file": path.name, "timestamp": suite.get("timestamp", ""), "tests": cases})
        except (ElementTree.ParseError, OSError):
            continue
    return {"reports": reports, "mode": "actual_pytest_reports"}
