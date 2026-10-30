# ShadQA test-case catalog

Prepared October 29, 2026. This is a source-informed baseline, not a claim of exhaustive coverage or a completed test run. Validate against the deployed build and agreed requirements before treating behavior as an approved acceptance criterion.

## Scope and execution rules

- **PUBLIC:** `https://shadqa.com` and `/demo`. `app/page.tsx` renders `RecordedDemo` on non-localhost hosts. This is a recorded showcase, not the live Python workspace.
- **LOCAL:** localhost frontend plus the Python API, using isolated test data/database. Record actual ports and build before execution. Never run mutation cases against shared data.
- Sources: `app/page.tsx`, `app/demo/page.tsx`, `components/recorded-demo.tsx`, `components/scenario-review.tsx`, `qa_pipeline/api.py`, `data/demo/*`, `public/demo/*`, and existing `browser_tests` and `tests`.
- Live browser inspection was unavailable during planning. Exact labels below come from source, not a fresh observation of production. New cases are **Not run**; existing Python tests are supporting design evidence, not proof this catalog passed.
- Shadman previously reported the Java hostname test passing. The current Java test opens the apex URL directly; it does not establish that the www redirect works.
- P1 = release-critical/core workflow; P2 = important supporting coverage; P3 = supplementary. Priority is separate from defect severity.
- **Smoke is a subset of regression.** Every case belongs to regression; the Smoke column selects the smaller suite. Do not duplicate tests into smoke/regression folders.
- Modes: UI = Selenium candidate; API = REST Assured candidate; Manual = human validation; Mixed = automation plus human judgment. Integration cases exercise real boundaries, not merely multiple clicks.
- For each execution record case ID, build/commit, environment, browser/version, data fixture, actual result, Pass/Fail/Blocked, defect ID, and evidence. Do not infer Pass from planned expected results.

## Public-site functional cases

Preconditions: deployed build available, fresh browser session, no login or private backend. Start each case independently. Wait for a meaningful page state rather than using fixed sleeps.

| ID | Pri | Smoke | Mode | Steps / data | Expected result |
| --- | --- | --- | --- | --- | --- |
| PUB-01 | P1 | Yes | UI | Open apex HTTPS homepage. | Final host is `shadqa.com`; visible H1 reads “Requirements. Reviewed. Tested.” after whitespace normalization; showcase controls visible. Host alone is insufficient. |
| PUB-02 | P1 | No | UI | Open `https://www.shadqa.com` independently. | Proposed canonical-host requirement: valid HTTPS then redirect to apex and correct page. Confirm intended hosting configuration; do not bypass TLS errors. |
| PUB-03 | P1 | Yes | UI | Navigate directly to `/demo`, then refresh. | Recorded showcase loads on both visits; default Walkthrough content visible. |
| PUB-04 | P1 | Yes | UI | Open homepage; inspect initial section and selection controls. | Walkthrough pressed; other section buttons not pressed; walkthrough heading and video present. |
| PUB-05 | P1 | Yes | UI | Click Evidence. | Evidence section visible; screenshot and recorded result summary present; Walkthrough content hidden. |
| PUB-06 | P1 | Yes | UI | Click Architecture. | “How the local system works,” verified live-run details, and recorded workflow checks visible. |
| PUB-07 | P1 | Yes | UI | Click Limits. | Scope limitations visible, including that hosted evidence cannot start tests or access private requirements. |
| PUB-08 | P2 | No | UI | Select Limits → Evidence → Walkthrough → Architecture; repeat a selection. | Exactly one section selected at a time; content matches it; no duplicate panels or stale content. |
| PUB-09 | P2 | No | UI | Select Evidence, then refresh `/demo`. | Current source resets to Walkthrough. Confirm this intended behavior rather than assuming section persistence. |
| PUB-10 | P2 | No | UI | Click SW/Shad Wayit identity link from homepage. | Navigates to `/demo`, preserving a usable showcase. |
| PUB-11 | P2 | No | UI/Manual | Inspect LinkedIn link and activate once. | Target is `https://www.linkedin.com/in/shad-wayit-msc/`; separate browsing context opens. Assert destination, not LinkedIn page content; close child context afterward. |
| PUB-12 | P1 | No | Mixed | Inspect Evidence summary and Limits language. | Recorded timestamp/scope visible; historical result is not represented as a newly executed or complete-coverage result. |
| PUB-13 | P2 | No | UI | Resize to 320×900, 390×844, and 1440×900; visit each section. | No horizontal page overflow; controls/content remain operable; long hashes wrap without hiding content. |
| PUB-14 | P2 | No | UI/Manual | Open unknown path `/nonexistent-qa-case`. | Proposed requirement: clear not-found outcome rather than false successful content; confirm routing contract. |

## Media, artifacts, and data integration

Preconditions: PUBLIC, clean download directory per test. Download to temporary locations; do not execute downloaded Python. Use HTTP/API assertions for assets rather than automating browser chrome.

| ID | Pri | Smoke | Mode | Steps / data | Expected result |
| --- | --- | --- | --- | --- | --- |
| ART-01 | P1 | Yes | UI | Open Walkthrough; wait for video metadata. | Video visible, no media error, finite positive duration and nonzero dimensions. Exact duration is not a stable acceptance criterion. |
| ART-02 | P2 | No | Mixed | Start playback with user action, pause, seek to valid time, resume. | Time advances while playing, pauses, and resumes after seeking; controls usable. |
| ART-03 | P2 | No | UI/API | Open full-size video link and download HD recording. | Correct `/demo/walkthrough-hd.webm` resource; nonempty playable WebM; no HTML fallback/error page. |
| ART-04 | P1 | Yes | UI | Open Evidence; wait for screenshot load. | Image has descriptive alternative text, completed load, and positive natural dimensions. |
| ART-05 | P2 | No | UI/API | Open full screenshot link. | Destination `/demo/generated-result.png`; valid nonempty image. |
| ART-06 | P1 | No | API | Retrieve `/demo/result.json`. | Successful response, valid JSON with timestamp, counts, scope, run ID, and plan hash of expected types; no HTML fallback. |
| ART-07 | P1 | No | UI+API integration | Retrieve recorded result; open Evidence and compare displayed fields. | Counts, seconds, timestamp, scope, run ID, and plan hash agree with that release’s fixture. Normalize formatting; do not hardcode historical counts as universal requirements. |
| ART-08 | P2 | No | UI+API integration | Download recorded result from Evidence; parse file. | Download is valid JSON and agrees with served result fixture. |
| ART-09 | P2 | No | UI/API | Download generated Python. | `/demo/test_guest_navigation.py` returns nonempty Python text, not HTML; content inspected without execution. |
| ART-10 | P2 | No | UI+API integration | Download workflow and benchmark JSON from Architecture; compare with displayed values. | Valid JSON; displayed statuses, event details and matched/total agree with fixtures. |
| ART-11 | P1 | No | Integration | In isolated preview, make private `/qa-api/**` unavailable and exercise all showcase sections. | Recorded showcase and assets still work without the Python backend; no live execution attempted. |
| ART-12 | P2 | No | Mixed | In preview, fail a media request or return malformed fixture data. | Proposed resilience requirement: page remains navigable and avoids false success claims; missing-media/error feedback assessed. Confirm UX; report current gaps rather than assuming implementation. |

## Local interactive workflow

Preconditions: LOCAL frontend/API running; isolated database and requirements fixture; stable approved target for any browser execution. No paid model calls. Reset fixtures independently per case. These are separate from production showcase tests.

| ID | Pri | Smoke | Mode | Steps / data | Expected result |
| --- | --- | --- | --- | --- | --- |
| LOC-01 | P1 | Local | UI | Open local `/`; inspect stage controls and default example. | Local QA workspace visible with Requirement/Evidence/Review/Python test/Results; prepared AUTH-04 example selected. |
| LOC-02 | P2 | No | UI | Switch between AUTH-04 and keyboard example; return to first. | Requirement/scenario match selected example; stage resets to Requirement and approval is cleared for the prepared UI state. |
| LOC-03 | P1 | No | UI+API integration | Search evidence for supported requirement using isolated source fixture. | Returned evidence matches API data and includes source identification; retrieval is not described as live LLM generation. |
| LOC-04 | P1 | No | UI+API integration | Create structured sample, edit one expected result, save, reload. | Saved revision and edited text persist through UI/API/storage boundary. |
| LOC-05 | P1 | No | UI+API integration | Approve saved structured revision; reload. | Approval and exact revision persist; approved package available. |
| LOC-06 | P1 | No | UI/API | Edit an approved review; inspect unsaved state, then save. | Unsaved changes block actions relying on prior approval; saving advances revision and clears approval. |
| LOC-07 | P1 | No | API/integration | Two clients load same revision; first saves; second submits stale revision. | Stale write rejected without overwriting newer data; exact status/body checked against API contract. |
| LOC-08 | P1 | No | UI/API | Change source fixture after approval; refresh/reload evidence. | Stale evidence indicated; dependent approval/execution cannot silently use changed sources. |
| LOC-09 | P1 | No | UI+API integration | Approve supported sample, preview Python, download it. | Preview and downloaded code match; package revision/source identity corresponds to reviewed state. |
| LOC-10 | P1 | No | UI/API | Attempt preview/export before approval. | Approval-gated actions disabled/rejected; no approved output falsely produced. |
| LOC-11 | P1 | No | UI/API | Include supported navigation plus unsupported scenario. | Unsupported scenario remains explicitly manual-only, not silently reported as executed. |
| LOC-12 | P1 | No | UI/API | Preview valid code without execution consent; attempt run. | No browser execution without separate execution approval. |
| LOC-13 | P1 | No | Integration | In disposable test environment only, approve supported code and execution, run, inspect history and artifacts. | Real job status and matching report/screenshot/trace recorded; history persists after reload. Confirm target/run permission before execution. |
| LOC-14 | P2 | No | UI/integration | Seed interrupted run with no artifacts; inspect Results/history. | Interrupted state displayed honestly with no-artifacts message; no false passed result or broken evidence assumption. |
| LOC-15 | P2 | No | UI | Stop/mock backend while editing review, attempt save. | Visible service failure; unsaved text retained; no false save confirmation. |
| LOC-16 | P2 | No | UI/API | Submit whitespace-only paragraph review; test 8000 and 8001 character boundaries. | Empty save blocked; UI maximum enforced. Determine API boundary behavior from schema before assigning exact status expectations. |
| LOC-17 | P2 | No | UI/API | Mock malformed response and timeout in preview. | Action finishes with understandable error; no false approval/save; recovery possible. |

## REST Assured API candidates

LOCAL only. Read `qa_pipeline/api.py` request/response schemas before coding. Do not guess status codes. Use disposable fixtures, no live model calls, and no real browser execution unless separately planned.

| ID | Pri | Smoke | Mode | Steps / data | Expected result |
| --- | --- | --- | --- | --- | --- |
| API-01 | P1 | Local | API | GET `/health`. | Healthy response agrees with documented implementation; response schema verified. |
| API-02 | P1 | No | API | POST `/retrieve` with valid query, no-match query, empty query, and invalid type as separate cases. | Valid matches/no-match results reflect fixture; invalid requests rejected according to schema without server crash. |
| API-03 | P1 | No | API | Create/read/update/approve structured review using supported fixture and exact revision. | Responses and subsequent GET show consistent revision, draft, evidence and approval state. |
| API-04 | P1 | No | API | Submit malformed JSON, missing required fields, and wrong field types separately. | Contract-consistent client errors; state unchanged; no private exception details leaked. |
| API-05 | P2 | No | API | GET unknown workflow and unknown run IDs separately. | Contract-consistent missing-resource response; no unrelated resource returned. |
| API-06 | P1 | No | API/integration | Request export and preview for approved supported revision; repeat after an edit. | Outputs bound to current approved state; invalidated revision cannot reuse stale approval. |
| API-07 | P2 | No | API | GET evidence/artifact for valid run, missing artifact and traversal-like path in isolated fixture. | Only allowed artifacts within intended scope served; missing/invalid paths handled safely. |
| API-08 | P1 | No | API | Attempt generated run without valid approval/plan identity using mocked worker. | Request rejected; worker never starts; no side effects. |

## Accessibility, compatibility, and release checks

PUBLIC unless stated. These are proposed quality checks, not a Section 508 conformance verdict. Confirm applicable standard/version and media requirements before compliance assessment.

| ID | Pri | Smoke | Mode | Steps / data | Expected result |
| --- | --- | --- | --- | --- | --- |
| ACC-01 | P1 | No | Manual/UI | Navigate all showcase sections and links using Tab/Shift+Tab and Enter/Space where appropriate. | All actions operable without mouse, logical order, no keyboard trap, visible focus. |
| ACC-02 | P2 | No | Mixed | Inspect accessible names, main/heading structure, section control group and pressed states. | Names meaningful; selected state exposed; content structure understandable with assistive technology. |
| ACC-03 | P2 | No | Manual | Read page and change sections with screen reader. | Content and current section understandable; no misleading state or inaccessible core action. |
| ACC-04 | P2 | No | Manual/tool | Measure text/control contrast and inspect focus indicators in all states. | Meet agreed applicable criteria; visual inspection alone is insufficient for numeric contrast. |
| ACC-05 | P2 | No | Manual | Zoom to 200%; check narrow reflow at equivalent 320 CSS-pixel width. | Text/content remains usable without clipping or loss of functionality; record exceptions against applicable criteria. |
| ACC-06 | P1 | No | Manual | Review recording with sound off and inspect audio/visual content alternatives. | Assess captions, transcript/audio-description needs against applicable requirements; missing alternatives recorded as gaps, not assumed present. |
| ACC-07 | P2 | No | Tool+Manual | Run automated accessibility scan, then manually validate findings and untested criteria. | Findings triaged with evidence; clean scan never labeled full conformance. |
| REL-01 | P2 | No | UI/Manual | Repeat core showcase cases on agreed Chrome/Firefox/Safari and desktop/mobile viewport matrix. | Core actions/media usable; browser-specific deviations documented. |
| REL-02 | P2 | No | Manual/tool | Measure homepage and media loading under agreed preview network conditions. | Record baseline and agreed budget before pass/fail; no invented universal response-time threshold. No production load test. |
| REL-03 | P1 | No | CI/review | Build preview; run selected smoke cases; retain reports and screenshot on failure. | Release evidence identifies build/environment; required failures stop promotion according to agreed gate policy. |
| REL-04 | P2 | No | Scan/review | Scan appropriate application/test source and inspect quality/security results. | Findings triaged; configured quality gate evaluated; secrets absent; coverage imported only from actual instrumentation/report. SonarQube does not prove UI correctness. |

## First automation sequence

1. PUB-01: strengthen current hostname test with visible heading and explicit wait.
2. PUB-05/06/07: parameterized section-content checks.
3. ART-04: screenshot-load assertion.
4. Extract page object and browser lifecycle helper after repetition demonstrates value.
5. Add smoke selection and full regression selection using the chosen framework, without duplicate tests.
6. Add read-only API artifact checks, then local API/integration cases with isolated fixtures.

Prefer feature-based test classes and separate page/support code. No test code, dependency changes, or folder moves are part of this catalog creation.

## Execution record template

| Case ID | Build | Environment | Browser | Data fixture | Actual result | Status | Evidence / defect |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Fill per run | | | | | | Not run | |

## Open decisions / exclusions

- Verify deployed content agrees with source and confirm www canonicalization/TLS requirements.
- Confirm not-found UX, media-error UX, performance budgets, browser matrix and applicable accessibility criteria before calling related proposals defects.
- Decide JUnit modernization versus TestNG before implementing suite grouping; Cucumber is optional and not explicitly required by the job.
- No login, signup, payment, wallet, or ICAM functionality is established on this portfolio. Do not fabricate those cases. ICAM remains interview scenario practice unless a real target is supplied.
- NoiseLabz is a separate product. Its guest navigation appears in recorded artifacts; this catalog does not claim current NoiseLabz product coverage.
- Paid live-AI evaluation, penetration testing, production load, real account changes, and production remote execution are outside this exercise.
- Every matrix row with multiple inputs requires separate execution results per input; expand into parameterized cases during implementation.
