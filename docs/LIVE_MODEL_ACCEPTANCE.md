# Live model acceptance

The portfolio and fixture demo work without an API key. Real model quality
remains unverified until the checks below are completed. This guide describes
the existing local integration; it does not enable paid calls automatically.

## Configure locally

Set `OPENAI_API_KEY`, `QA_MODEL`, and `QA_ENABLE_LIVE_MODEL=1` in the terminal
where you run the Python command. Use a model available to your API account
that supports Structured Outputs. The CLI does not automatically read `.env`.
Keep the key out of chat, source control, screenshots, and the browser.

Confirm the private requirements are at `outputs/requirements.md`, or set
`QA_REQUIREMENTS_PATH` to their location. Agree a spending limit before running.
The application caps requests and output tokens, not dollars.

## First live example

```sh
.venv/bin/python -m qa_pipeline.run_workflow --live --confirm-live
```

This sends retrieved evidence to the provider and makes at most two requests:
author and reviewer. There are no automatic retries or test execution. A failed
request can still be charged. Inspect the saved workflow before retrying.

Load the printed workflow ID in the local Review panel. Check its draft and
stage log before replacing the saved guest draft. Importing replaces that
draft and leaves it unapproved. Reload the structured review after import.

## Record three independently reviewed runs

For each run, record the workflow ID, model, token usage, elapsed time, and
actual cost from the provider's usage records. Do not infer cost from tokens
without the applicable pricing. Keep this evidence privately under `outputs/`.

| Check | Acceptance |
| --- | --- |
| Evidence | Every citation exists and supports the associated assertion |
| Scope | No invented product behavior or unsupported wallet requirements |
| Coverage | Missing cases and ambiguities are explicitly recorded |
| Reviewer | Corrections improve support without introducing assumptions |
| Approval | Imported output remains unapproved until a human reviews it |
| Compilation | Unsupported prose is rejected; rejection is not a model-quality verdict |
| Execution | Only reviewed supported code runs after separate execution approval |
| Failure | Failed calls stop without retrying or automatically running tests |

The three runs are a small acceptance sample, not a model-accuracy benchmark.
Use the existing mocked tests to inspect refusal, timeout, malformed output,
and invalid citation behavior without paying to provoke provider failures.

## Present the result honestly

Keep the existing recorded showcase while evaluating live output. Update its
claims only after retaining reviewed evidence. The public site contains curated
artifacts; the Python runner and private requirements remain local.

For employer sharing, the existing Site supports public link access or invited
viewers. Choose the intended audience before changing owner-only access.
