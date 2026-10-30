"""Read bounded local pytest reports; never execute submitted code."""
from pathlib import Path
import re
from xml.etree import ElementTree


def case_description(name):
    mappings = [
        ("test_guest_can_open_features", "NAV-01", "Guest opens Features"),
        ("About Us", "NAV-02", "About Us navigation"),
        ("How It Works", "NAV-03", "How It Works navigation"),
        ("Roadmap", "NAV-04", "Roadmap navigation"),
        ("test_features_link_can_be_activated", "KEY-01", "Features link works with Tab and Enter"),
        ("test_mobile_menu_opens", "MOB-01", "Mobile menu opens and selects Features"),
        ("test_mobile_menu_is_keyboard", "KEY-02", "Mobile menu is keyboard reachable"),
    ]
    for match, identifier, title in mappings:
        if match in name:
            return identifier, title
    return None, name


def screenshot_for(directory, report, case, filenames=("test-failed-1.png", "test-finished-1.png")):
    # Match pytest-playwright's ASCII artifact naming for this suite exactly.
    classname = case.get("classname", "")
    if classname != "browser_tests.test_noiselabz":
        return None
    slug = re.sub(r"[^a-z0-9]+", "-", f"browser_tests/test_noiselabz.py::{case.get('name', '')}".lower()).strip("-")
    folder = directory / report.stem / slug
    for filename in filenames:
        path = folder / filename
        if path.is_file() and path.resolve().is_relative_to(directory.resolve()):
            return f"/qa-api/browser-artifacts/{report.stem}/{slug}/{filename}"
    return None


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
                name = case.get("name", "Unnamed test")
                identifier, title = case_description(name) if case.get("classname") == "browser_tests.test_noiselabz" else (None, name)
                cases.append({"name": name, "status": status, "case_id": identifier,
                              "title": title, "screenshot": screenshot_for(directory, path, case), "trace": screenshot_for(directory, path, case, ("trace.zip",))})
            reports.append({"file": path.name, "timestamp": suite.get("timestamp", ""), "tests": cases})
        except (ElementTree.ParseError, OSError):
            continue
    return {"reports": reports, "mode": "actual_pytest_reports"}
