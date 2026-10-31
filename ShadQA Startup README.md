# ShadQA - Local Startup and Interview Demo

Prepared October 30, 2026

Use a separate terminal for each long-running service. Leave its terminal open.
Run commands one at a time. Do not type the explanatory text as commands.
These are existing-installation instructions, not a fresh-machine setup.

### Quick Map

Public website: https://shadqa.com
Local frontend: usually http://localhost:5173 (use the URL npm prints)
Recorded local showcase: http://localhost:5173/demo
Python API documentation: http://127.0.0.1:8000/docs
SonarQube dashboard: http://localhost:9000

For a simple demo, use the public website or local /demo.
Start the Python API for local API tests or the interactive workspace.
Start SonarQube only for analysis/dashboard work.
Start the self-hosted runner only for the GitHub SonarQube job.

## Terminal 1 - Python Api (Port 8000)

1. Go to the repository root:

```sh
cd /Users/shadman/Documents/Projects/shad-wayit-ai-qa-lab-main
```

2. Start the API with the known practice fixture:

```sh
QA_REQUIREMENTS_PATH="$PWD/api-test-requirements.md" .venv/bin/python -m uvicorn qa_pipeline.api:app --host 127.0.0.1 --port 8000
```

What it means:
- QA_REQUIREMENTS_PATH selects the file the API searches.
- $PWD is the current directory, which must be the repository root here.
- .venv/bin/python selects the project's Python environment directly.
- Uvicorn serves the FastAPI application at port 8000.
- You do not need to activate .venv separately for this command.

Expected: Application startup complete; Uvicorn running on 127.0.0.1:8000.
Leave this terminal running.

3. Open in Chrome:

http://127.0.0.1:8000/docs

4. Manual API check: POST /retrieve -> Try it out -> enter this body -> Execute:

```json
{
  "query": "AUTH-04",
  "limit": 1
}
```

Expected: HTTP 200, status matches_found, evidence for AUTH-04.
The fixture must exist and contain:
**AUTH-04** Browse without a wallet.

IMPORTANT: This small fixture supports our Java retrieval API tests. It is NOT
the complete private requirements document needed for every interactive QA
workflow. For a full local workflow, start the server with the appropriate
complete requirements source instead. Do not upload private requirements.

GET / and GET /favicon.ico returning 404 are expected if no routes exist there.
503 with "Requirements source is unavailable or invalid" means inspect the
configured source file/path. It does not mean change the test to expect success.

## Terminal 2 - Portfolio Frontend

1. Go to the repository root:

```sh
cd /Users/shadman/Documents/Projects/shad-wayit-ai-qa-lab-main
```

2. Start the existing frontend development setup:

```sh
npm run dev
```

3. Open the Local URL printed in the terminal. Usually:

http://localhost:5173

Keep the literal localhost/127.0.0.1 hostname for the local workspace.
The app chooses its hosted view based on the hostname.

Local /: interactive QA workspace; backend required for its API actions.
Local /demo: recorded showcase; not a live execution service.

http://localhost:5173/demo

Public website: https://shadqa.com
Public recorded JSON: https://shadqa.com/demo/result.json

The public showcase does not need your laptop's Python API to display its
published artifacts. Java UI tests currently target the public website,
not this local frontend.

## Terminal 3 - Sonarqube Server (Optional, Port 9000)

1. Go to the repository root:

```sh
cd /Users/shadman/Documents/Projects/shad-wayit-ai-qa-lab-main
```

2. Start the server from its CURRENT installation location:

```sh
./selenium/.tools/sonarqube-26.10.0.133078/bin/macosx-universal-64/sonar.sh console
```

Expected: SonarQube is operational.
Leave this terminal running.

3. Open the dashboard:

http://localhost:9000

Sign in with your configured local credentials. Do not put passwords/tokens
in these notes. Existing analysis remains available without a new scan.

Starting the server does NOT start a scan. Do not move its installation while
it is running; stop it gracefully first.

If necessary, its graceful stop command from the repository root is:

```sh
./selenium/.tools/sonarqube-26.10.0.133078/bin/macosx-universal-64/sonar.sh stop
```

## Terminal 4 - Github Self-Hosted Runner (Optional)

1. Go to the registered runner folder:

```sh
cd /Users/shadman/Documents/Projects/shad-wayit-ai-qa-lab-main/.tools/actions-runner
```

2. Start listening for GitHub jobs:

```sh
./run.sh
```

Expected: Connected to GitHub; Listening for Jobs.
Leave this terminal running. After a job completes, listening continues.
Do not start a second copy if a runner session is already active.

Runner labels: self-hosted, macOS, ARM64, sonarqube-local.
For the SonarQube job, both this runner AND the SonarQube server must run.
Your Mac must be awake, connected, and have sufficient disk space.

The runner uses its own checkout under _work. Local ignored downloads are
not automatically present in that checkout; the workflow currently uses an
absolute path to your installed Maven.

## Terminal 5 - Java Test Commands

1. Go to the INNER Maven project, where pom.xml is:

```sh
cd /Users/shadman/Documents/Projects/shad-wayit-ai-qa-lab-main/selenium/selenium
```

2. Choose the command you need. These commands RUN tests.

### All Homepage Ui Tests

Needs Chrome and access to the public website, not local Uvicorn:

```sh
../.tools/apache-maven-3.9.12/bin/mvn -Dtest=com.shadqa.tests.ui.HomePageTest test
```

ONE UI METHOD (example; use the exact method name in your class):

```sh
../.tools/apache-maven-3.9.12/bin/mvn '-Dtest=com.shadqa.tests.ui.HomePageTest#shouldDisplayHomepageForBothAddresses' test
```

### Public Json-Resource Api Tests

Needs public website access; no browser or local API:

```sh
../.tools/apache-maven-3.9.12/bin/mvn -Dtest=com.shadqa.tests.api.RecordedResultApiTest test
```

### Local Evidence Api Tests

Needs Terminal 1 running with api-test-requirements.md:

```sh
../.tools/apache-maven-3.9.12/bin/mvn -Dtest=com.shadqa.tests.api.EvidenceApiTest test
```

### Performance Baseline

Needs Terminal 1 and its practice fixture. Sequential timing, not load testing:

```sh
../.tools/apache-maven-3.9.12/bin/mvn -Dtest=com.shadqa.tests.performance.EvidencePerformanceTest test
```

SMOKE TAG:

```sh
../.tools/apache-maven-3.9.12/bin/mvn -Dgroups=smoke test
```

### Regression Tag

Includes local-service tests and the regression-tagged performance baseline:

```sh
../.tools/apache-maven-3.9.12/bin/mvn -Dgroups=regression test
```

### All Discovered Tests

Needs every relevant dependency/environment, including the local API:

```sh
../.tools/apache-maven-3.9.12/bin/mvn test
```

COMPILE ONLY - NO TEST EXECUTION:

```sh
../.tools/apache-maven-3.9.12/bin/mvn test-compile
```

Reports: selenium/selenium/target/surefire-reports/ relative to repository root.
target is generated. Do not edit its class files or reports as source code.

## Optional Manual Sonarqube Scan - Does Not Run Tests

Keep Terminal 3 running. Use another terminal in the inner Maven project:

```sh
cd /Users/shadman/Documents/Projects/shad-wayit-ai-qa-lab-main/selenium/selenium
```

Read the existing analysis token privately (zsh command):

```sh
read -s "SONAR_TOKEN?Paste SonarQube token: "
```

At the prompt paste the token, then press Enter. Input is hidden.
Do not replace the prompt text inside the command with your token.

```sh
export SONAR_TOKEN
```

Run the scan:

```sh
../.tools/apache-maven-3.9.12/bin/mvn clean test-compile \
  org.sonarsource.scanner.maven:sonar-maven-plugin:sonar \
  -Dsonar.projectKey=shadqa-java-automation \
  -Dsonar.projectName="ShadQA Java Automation" \
  -Dsonar.host.url=http://localhost:9000 \
  -Dsonar.qualitygate.wait=true
```

This clean command removes generated target output, including old test reports.
The scan compiles test code but does not execute browser or API tests.
It waits for the quality gate; an applicable failed gate fails the command.
No coverage report is produced by this command.

Clear the token from that terminal when finished:

```sh
unset SONAR_TOKEN
```

GitHub-triggered scanning uses its SONAR_TOKEN repository secret instead.
It does not require this terminal environment variable to remain set.

## Troubleshooting And Stopping

"No such file or directory": check pwd. Relative commands depend on location.

```sh
pwd
```

"Address already in use" or "already running": do not launch duplicates.
Check listeners (read-only):

```sh
lsof -nP -iTCP:8000 -sTCP:LISTEN
```

```sh
lsof -nP -iTCP:9000 -sTCP:LISTEN
```

Connection refused: confirm the service is running at the test's exact URL.
API 422: inspect request format/fields and returned validation details.
API 503: verify requirements source exists and restart with correct configuration.
Queued Sonar job: check runner online status and all requested labels.
Failed Sonar job: read the failed step; do not assume a quality-gate failure.

Git output showing (END): press q to exit its pager.
To print diffs directly:

```sh
git --no-pager diff
```

Stop each foreground service using Ctrl+C in its own terminal.
Stopping a process does not delete its files. Do not delete lock/database files.
deactivate only exits an activated Python environment; it does not stop Uvicorn.

## Before Monday'S Interview

- Start only the services needed for the intended demonstration.
- Verify Chrome, camera/microphone and entire-screen sharing beforehand.
- Know which site is public, which is local, and which fixture is loaded.
- Keep required services open and the Mac awake.
- Close AI assistants and disable AI coding assistance during the interview,
  as required by the interview policy. Use these notes for preparation and
  follow the interviewer's rules about resources during the session.
- Do not trigger paid live-model calls or unrelated execution for a demo.
- Explain what each command does before running it.

One-sentence architecture explanation:
"The frontend displays the QA workspace, FastAPI serves the local API,
Maven runs my Java tests, and the self-hosted GitHub runner submits scans
to my local SonarQube server. Each process has a different responsibility."
