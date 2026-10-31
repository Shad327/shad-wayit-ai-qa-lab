# Java automated test case register

Last reviewed: October 31, 2026.

Scope: the 20 JUnit test methods in `java/com/shadqa/tests/`: 11 UI, 8 API, and 1 performance. This register describes implemented assertions, not an execution result or complete requirements coverage. Requirement references below come from the Java test comments; they have not been independently validated against a full requirements document.

Each case ID is stable. The linked class and exact method name identify its automation. Class-level tags apply to every method: all 20 cases are `regression`; four UI cases also have `smoke`.

## Environments and preconditions

| Key | Required setup |
| --- | --- |
| UI | Chrome installed; internet access to `https://shadqa.com` and, for UI-001, `https://www.shadqa.com`. Tests create and close their own browser. Local frontend and Python API are unnecessary. |
| PUBLIC | Internet access to `https://shadqa.com`; no browser or local API required. |
| LOCAL | FastAPI running at `http://127.0.0.1:8000` with repository-root `api-test-requirements.md` selected through `QA_REQUIREMENTS_PATH`. Fixture includes `**AUTH-04** Browse without a wallet.` and excludes AUTH-99. |

See [startup instructions](../../../../ShadQA%20Startup%20README.md) for service commands. Java execution requires the project's Java 21 and Maven setup.

## UI cases

Automation: [HomePageTest.java](java/com/shadqa/tests/ui/HomePageTest.java). Every case starts at the public homepage unless its steps specify another route. Steps are performed in order.

| Case ID | Requirement reference | Tags | Setup | Steps / input | Expected result actually checked | Automated method |
| --- | --- | --- | --- | --- | --- | --- |
| UI-001 | PUB-01 | smoke, regression | UI | Open each apex and www homepage. | Main heading is `Requirements. Reviewed. Tested.`; exactly four visible, enabled controls appear in order: Walkthrough, Evidence, Architecture, Limits. No specific redirect destination asserted. | `shouldDisplayHomepageForBothAddresses` |
| UI-002 | PUB-15 | regression | UI | Capture initial URL; select Evidence, Architecture, Limits, Walkthrough. | URL equals captured URL after each selection. | `shouldKeepUrlUnchangedWhenSelectingSections` |
| UI-003 | PUB-05, PUB-06, PUB-07, PUB-08 (grouped reference) | smoke, regression | UI | Select Evidence, Architecture, Limits, Walkthrough in order. | Selected control has `aria-pressed=true`; visible section headings respectively match `One generated test · passed`, `How the local system works`, `What this demo proves—and what it does not`, `From approved scenario to a real browser run`. | `shouldDisplayExpectedHeadingForEachSection` |
| UI-004 | ART-04 | smoke, regression | UI | Select Evidence; inspect its screenshot. | Screenshot is displayed, `complete=true`, and `naturalWidth>0`. | `shouldDisplayLoadedEvidenceScreenshot` |
| UI-005 | PUB-10 | regression | UI | Click brand logo; reopen homepage; click Shad Wayit brand name. | Each click reaches path `/demo` and displays main heading `Requirements. Reviewed. Tested.`. | `shouldOpenDemoFromLogoAndName` |
| UI-006 | PUB-09 | regression | UI | Open `/demo`; select Evidence and wait for its section; refresh. | Walkthrough control has `aria-pressed=true` after refresh. No post-refresh heading assertion. | `shouldRestoreWalkthroughAfterRefresh` |
| UI-007 | ART-01 | smoke, regression | UI | Inspect the initial Walkthrough video. | Video is displayed; `readyState>=1`; intrinsic width is positive; duration is finite and positive. Playback is not checked. | `shouldLoadWalkthroughVideoMetadata` |
| UI-008 | PUB-11 | regression | UI | Inspect LinkedIn link attributes. | `href=https://www.linkedin.com/in/shad-wayit-msc/` and `target=_blank`. | `shouldConfigureLinkedInProfileLink` |
| UI-009 | PUB-11 | regression | UI | Verify LinkedIn href; capture window handles; click link. | Correct profile href; window count increases by one within 10 seconds; exactly one new handle exists. LinkedIn page content is not checked. | `shouldOpenLinkedInInNewTab` |
| UI-010 | ART-05 | regression | UI | Select Evidence; click screenshot; switch to new browsing context. | Window count increases by one within 10 seconds; destination path becomes `/demo/generated-result.png`. Image content in the new context is not checked. | `shouldOpenFullEvidenceScreenshot` |
| UI-011 | PUB-13 | regression | UI | Set browser window to 390 × 844; select Evidence, Architecture, Limits, Walkthrough and wait for each section. | For each section, document scroll width is no greater than `window.innerWidth`. This is a window size, not a guaranteed exact viewport size; full mobile usability is not checked. | `shouldAvoidHorizontalOverflowOnNarrowScreen` |

## API cases

All requests accept JSON. Local POST requests also send JSON content type. Local failure assertions log responses when validation fails.

| Case ID | Requirement reference | Tags | Setup | Steps / input | Expected result actually checked | Automation |
| --- | --- | --- | --- | --- | --- | --- |
| API-001 | API-02a | regression, local | LOCAL | POST `/retrieve` with `{"query":"AUTH-04","limit":1}`. | HTTP 200; JSON; query AUTH-04; status `matches_found`; exactly one result; result ID AUTH-04 and text `**AUTH-04** Browse without a wallet.`. | [EvidenceApiTest](java/com/shadqa/tests/api/EvidenceApiTest.java) — `shouldReturnEvidenceForValidQuery` |
| API-002 | API-02b | regression, local | LOCAL | POST `/retrieve` with `{"query":"   ","limit":1}`. | HTTP 422; JSON; nonempty detail list; first detail location includes `query`. | [EvidenceApiTest](java/com/shadqa/tests/api/EvidenceApiTest.java) — `shouldRejectBlankQuery` |
| API-003 | API-02c | regression, local | LOCAL | POST `/retrieve` with `{"query":"AUTH-04","limit":11}`. | HTTP 422; JSON; nonempty detail list; first detail location includes `limit`. | [EvidenceApiTest](java/com/shadqa/tests/api/EvidenceApiTest.java) — `shouldRejectLimitAboveMaximum` |
| API-004 | API-02d | regression, local | LOCAL | POST `/retrieve` with `{"query":"AUTH-99","limit":1}`. | HTTP 200; JSON; query AUTH-99; status `no_evidence`; empty results. | [EvidenceApiTest](java/com/shadqa/tests/api/EvidenceApiTest.java) — `shouldReturnNoEvidenceForUnmatchedQuery` |
| API-005 | API-02e | regression, local | LOCAL | POST `/retrieve` with `{"limit":1}`. | HTTP 422; JSON; nonempty detail list; first detail location includes `query` and type equals `missing`. | [EvidenceApiTest](java/com/shadqa/tests/api/EvidenceApiTest.java) — `shouldRejectMissingQuery` |
| API-006 | API-SEC-01 | regression, local | LOCAL | POST `/retrieve` with `{"query":"AUTH-04","limit":1,"source":"another-file.md"}`. | HTTP 422; JSON; first detail location includes `source` and type equals `extra_forbidden`. | [EvidenceApiTest](java/com/shadqa/tests/api/EvidenceApiTest.java) — `shouldRejectCallerSuppliedSource` |
| API-007 | ART-06 | regression | PUBLIC | GET `/demo/result.json`. | HTTP 200; JSON; `tests>=0`. Required identifiers and other counts are not asserted despite the broader source comment. | [RecordedResultApiTest](java/com/shadqa/tests/api/RecordedResultApiTest.java) — `shouldReturnValidRecordedResult` |
| API-008 | ART-10 | regression | PUBLIC | GET `/demo/workflow.json`. | HTTP 200; JSON; mode and status are nonempty strings; events is a list. Event contents and specific mode/status values are not asserted. | [RecordedResultApiTest](java/com/shadqa/tests/api/RecordedResultApiTest.java) — `shouldReturnRecordedWorkflow` |

## Performance case

| Case ID | Requirement reference | Tags | Setup | Steps / input | Expected result actually checked | Automation |
| --- | --- | --- | --- | --- | --- | --- |
| PERF-001 | PERF-01 | regression, performance, local | LOCAL | POST `/retrieve` with `{"query":"AUTH-04","limit":1}` once for warm-up, then five times sequentially. Sort measured durations; print each duration, median, and slowest in milliseconds. | Every request, including warm-up, returns HTTP 200, JSON, status `matches_found`, and first result ID AUTH-04. Timing is recorded; no latency threshold or load/concurrency target is enforced. | [EvidencePerformanceTest](java/com/shadqa/tests/performance/EvidencePerformanceTest.java) — `shouldMeasureSearchResponseTimes` |

## Running and recording evidence

Run from `selenium/selenium`:

```sh
# All 20 cases; LOCAL, UI, and PUBLIC setup required
../.tools/apache-maven-3.9.12/bin/mvn test

# Four smoke UI cases
../.tools/apache-maven-3.9.12/bin/mvn -Dgroups=smoke test

# All 20 regression cases
../.tools/apache-maven-3.9.12/bin/mvn -Dgroups=regression test

# One case: replace class and method with the table's automation reference
../.tools/apache-maven-3.9.12/bin/mvn '-Dtest=com.shadqa.tests.api.EvidenceApiTest#shouldReturnEvidenceForValidQuery' test
```

Maven evidence is generated under [target/surefire-reports](../../target/surefire-reports/). Reports are overwritten by later runs and removed by `clean`; preserve relevant reports with a run record before cleaning. IDE runs may use a different results location. Do not mark a case passed merely because it is automated.

Copy this table for each recorded run; add one row per executed case (or an explicit list of case IDs for a suite summary):

| Run ID | Date/time + timezone | Commit | Case ID(s) | Environment / fixture | Result (Pass / Fail / Blocked / Not run) | Evidence link | Defect / notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| To be assigned | — | — | — | — | Not run | — | No execution performed when this register was created. |

## Keeping the register current

1. Update this file in the same change as a test's inputs, assertions, tags, or dependencies. Treat Java assertions and page-object checks as the source of implemented behavior.
2. Keep case IDs stable when renaming methods; update the method and class link. Assign the next unused ID for a new case. Record removed cases as retired rather than reusing IDs.
3. Keep requirement references aligned with approved requirements and source comments. A shared requirement can have multiple cases; a grouped reference does not prove complete coverage of every requirement.
4. Include effective class and method tags. Recheck suite totals after adding/removing methods or changing tags. Current totals: 20 regression, 4 smoke, 7 local, 1 performance.
5. Record execution results separately using the run log, with commit, environment, evidence, and defect reference. Update the review date only after checking the register against source.
