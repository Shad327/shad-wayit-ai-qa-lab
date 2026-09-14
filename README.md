# Shad Wayit — AI QA Lab

A React/TypeScript portfolio and local Python QA pipeline for NoiseLabz public navigation. This is Shad's testing toolkit, not the NoiseLabz application.

## Working capabilities

- FastAPI + SQLite: source-backed lexical retrieval, structured scenario editing, revisioned approval, evidence freshness checks.
- Deterministic evaluation: schema/citation membership, duplicate steps, uncited passages, open questions and explicit human semantic review.
- Constrained Python Playwright generation: guest → Features, with optional About Us, How It Works and Roadmap steps. Arbitrary prose is rejected rather than guessed.
- Reviewed generated execution: exact plan identity, idempotent run IDs, timeout, filtered subprocess environment, saved code/report/screenshot/trace, latest-ten history.
- Separate seven-case hand-written public regression suite. A recorded mobile keyboard failure is evidence, not a NoiseLabz fix.
- Model adapter with mocked provider tests; live LLM generation is not connected to the demo. Retrieval is lexical, not a vector RAG system. No agent/subagent orchestration or code-aware repository analysis is claimed.

## Run locally

Use Python 3.12 and a supported Node runtime. From this project directory:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[test,browser]'
.venv/bin/python -m playwright install chromium
npm run install:ci
```

The private requirements document belongs at `outputs/requirements.md`; alternatively set `QA_REQUIREMENTS_PATH` for the Python service. No API key is needed for the template demo.

Start these in separate terminals:

```sh
.venv/bin/python -m uvicorn qa_pipeline.api:app --host 127.0.0.1 --port 8000
npm run dev
```

Open http://localhost:5173. Review → create sample → optionally add supported sections → save → inspect evaluation → approve → preview code → approve execution → run → Results.

## Verify

```sh
.venv/bin/python -m pytest tests -q
npx tsc --noEmit
npm run build
```

Browser tests require the local website. Tests use temporary review databases. The explicit live walkthrough visits only the public NoiseLabz site:

```sh
QA_TEST_GENERATED_RUN=1 .venv/bin/python -m pytest browser_tests/test_interview_walkthrough.py --browser chromium --video on
```

## Deployment boundary

The hosted portfolio is a recorded showcase. Python execution is local: Vite's `/qa-api` proxy is development-only. Never expose the local runner publicly as-is. A hosted runner requires authentication, authorization, request limits, a durable job worker, persistent artifact storage and an isolated execution environment. Sites Worker hosting does not run this Python/Chromium process.

Private requirements, resume, keys, SQLite databases and raw local outputs stay excluded from source publication. Curated public-demo artifacts must be explicitly exported. Live model accuracy, full product coverage and accessibility certification are not established by passing schema tests.
