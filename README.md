# Shad Wayit — AI QA Lab

React interface for a guided NoiseLabz requirements-to-test portfolio demo.

## Implemented

- Two prepared requirement examples grounded in the supplied PRD.
- Evidence display, editable scenarios, session-local approval invalidation.
- Approval-gated download of prepared Playwright Python templates.
- Honest execution status and actual interface activity log.
- Feature-detected read-only WebMCP state tool; runtime validation unavailable in this session.

## Not implemented yet

Local Python retrieval is now available in `qa_pipeline/`: it parses Markdown
requirements and returns lexical matches with source lines and a document hash.
Run `python -m qa_pipeline --source outputs/requirements.md --query AUTH-04`.
Install the test extra (`pip install 'pytest>=8,<9'`) and run `python -m pytest`.
The tests use synthetic inputs and do not require the private PRD. This component
is not yet connected to the React interface or exposed as an HTTP service.

Live LLM generation, automated RAG, backend approval enforcement, Python execution,
MCP server integration, evaluation results, or a recorded demo video.
The WebMCP browser tool is not the planned Python MCP server.
Templates do not automatically incorporate scenario edits and have not been run.

## Development

Use Node 22.13 or newer and npm. Run `npm run install:ci`, then `npm run dev`.
`npm run build` creates the Sites-compatible build. `npx tsc --noEmit` checks types.

The intended next service is a Python QA backend using pytest and Playwright.
The supplied private resume and planning documents in outputs/ are excluded from Git.
