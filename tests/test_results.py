from qa_pipeline.results import browser_reports


def test_report_statuses_are_not_all_reported_as_passes(tmp_path):
    (tmp_path / "browser-sample.xml").write_text('''<testsuites><testsuite timestamp="2026-09-10T23:00:00"><testcase name="pass"/><testcase name="fail"><failure/></testcase><testcase name="setup error"><error/></testcase><testcase name="skip"><skipped/></testcase></testsuite></testsuites>''')
    tests = browser_reports(tmp_path)["reports"][0]["tests"]
    assert [t["status"] for t in tests] == ["passed", "failed", "failed", "skipped"]


def test_invalid_and_non_browser_reports_not_displayed(tmp_path):
    (tmp_path / "browser-partial.xml").write_text("<testsuites>")
    (tmp_path / "python-tests.xml").write_text("<testsuite/>")
    assert browser_reports(tmp_path)["reports"] == []
