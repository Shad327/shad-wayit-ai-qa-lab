from qa_pipeline.results import browser_reports


def test_report_statuses_are_not_all_reported_as_passes(tmp_path):
    (tmp_path / "browser-sample.xml").write_text('''<testsuites><testsuite timestamp="2026-09-10T23:00:00"><testcase name="pass"/><testcase name="fail"><failure/></testcase><testcase name="setup error"><error/></testcase><testcase name="skip"><skipped/></testcase></testsuite></testsuites>''')
    tests = browser_reports(tmp_path)["reports"][0]["tests"]
    assert [t["status"] for t in tests] == ["passed", "failed", "failed", "skipped"]


def test_invalid_and_non_browser_reports_not_displayed(tmp_path):
    (tmp_path / "browser-partial.xml").write_text("<testsuites>")
    (tmp_path / "python-tests.xml").write_text("<testsuite/>")
    assert browser_reports(tmp_path)["reports"] == []


def test_case_id_and_screenshot_are_tied_to_report(tmp_path):
    name = "test_mobile_menu_is_keyboard_reachable[chromium]"
    folder = tmp_path / "browser-demo" / "browser-tests-test-noiselabz-py-test-mobile-menu-is-keyboard-reachable-chromium"
    folder.mkdir(parents=True)
    (folder / "test-failed-1.png").write_bytes(b"placeholder")
    (tmp_path / "browser-demo.xml").write_text(f'<testsuite><testcase classname="browser_tests.test_noiselabz" name="{name}"><failure/></testcase></testsuite>')
    case = browser_reports(tmp_path)["reports"][0]["tests"][0]
    assert case["case_id"] == "KEY-02"
    assert case["status"] == "failed"
    assert case["screenshot"].endswith("/test-failed-1.png")


def test_screenshot_symlink_outside_outputs_not_exposed(tmp_path):
    output = tmp_path / "outputs"
    folder = output / "browser-demo" / "browser-tests-test-noiselabz-py-test_mobile"
    output.mkdir()
    name = "test_mobile_menu_is_keyboard_reachable[chromium]"
    folder = output / "browser-demo" / "browser-tests-test-noiselabz-py-test-mobile-menu-is-keyboard-reachable-chromium"
    folder.mkdir(parents=True)
    secret = tmp_path / "private.png"
    secret.write_bytes(b"private")
    (folder / "test-failed-1.png").symlink_to(secret)
    (output / "browser-demo.xml").write_text(f'<testsuite><testcase classname="browser_tests.test_noiselabz" name="{name}"/></testsuite>')
    assert browser_reports(output)["reports"][0]["tests"][0]["screenshot"] is None
