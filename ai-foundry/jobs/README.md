# AI Foundry Batch

This is component #3's **core pipeline logic and offline/manual batch runner**.
It reads each per-client AIRL assessment workbook (`.xlsx`) from Blob `data/`,
runs it through the real `airl-pulse-report` skill pipeline in `../skill/`
(validate → build content model → LLM narrative draft → lint/validate →
render), and writes client-ready HTML reports to Blob `report/`.

**Production hosting note:** the monthly Logic App flow invokes
`../function/` (an Azure Function), not this script directly, for the
per-client report generation step. See `../function/README.md` for why: AI
Foundry Hub/Project workspaces do not support the classic `AmlCompute` compute
type that `job_definition.yaml` below assumes, so this component cannot
currently run as an AI Foundry / Azure ML job against `aif-scout-wus3` /
`aif-scout-hub-wus3`. `../function/function_app.py` imports and calls this
module's `process_client()` / `build_oai_client()` / `load_reference_text()`
directly (unchanged) — the pipeline logic lives here once; only the
production trigger/hosting differs.

`run_batch.py` remains useful as-is for:
- Manual/offline whole-month batch runs from a workstation or CI pipeline with
  the right Azure credentials (`az login` + RBAC), e.g. for backfills or
  reprocessing every client in one command.
- Local development and the smoke-testing workflow used to validate this
  pipeline end to end.
- A future home if a classic (non-Foundry-kind) Azure ML workspace with
  `AmlCompute` is ever provisioned for this project.

## Files

- `run_batch.py` — orchestrator: enumerates client workbooks for a
  `--run-month`, and per client:
  1. downloads and validates the workbook (`../skill/scripts/validate_workbook.py`),
  2. builds the deterministic content model (`../skill/scripts/build_content_model.py`),
  3. calls Azure OpenAI (gpt-4o, via Managed Identity) to draft narrative
     fields grounded in `../skill/SKILL.md` + `../skill/references/narrative_rules.md`
     + `../skill/references/output_contract.md` +
     `../skill/references/construct_composite_definitions.md`,
  4. lints and validates the merged content model
     (`../skill/scripts/lint_narrative_labels.py`,
     `../skill/scripts/validate_content_model.py`), feeding any issues back to
     the LLM for up to 2 additional repair passes,
  5. renders the final HTML (`../skill/scripts/render_report.py`) only once
     lint + validation are clean,
  6. retries the whole per-client attempt with exponential backoff on any
     failure (transient or unresolved narrative issues), writes outputs and a
     status manifest to Blob.

  All `../skill/scripts/*.py` calls are made as subprocesses against their CLI
  entrypoints -- the skill package's own files are never imported or modified,
  per `../README.md`'s "do not fork or edit files inside skill/" rule.
- `job_definition.yaml` — Azure Machine Learning command-job spec for running
  the whole-month batch on a classic AML compute cluster. **Not currently
  deployable** against `aif-scout-wus3` (Foundry Project kind); kept for a
  future classic AML workspace, or as a reference for running it under
  `az ml job create` with `--resource-group`/`--workspace-name` pointed at a
  compatible workspace.
- `requirements.txt` — Python deps for the batch entrypoint (also installed by
  `../function/requirements.txt` for the production Function App).

## Retry

Each client gets up to `retries.aiFoundryPerClient` attempts (default 4) with
exponential backoff: `2, 4, 8, 16` seconds. Within a single attempt, narrative
drafting itself gets up to 2 additional repair passes (issues from
lint/validate are fed back to the LLM) before the attempt is considered
failed. If a client fails all outer attempts the run continues on remaining
clients, and the failed client is recorded in
`report/<slug>/status-<MMYYYY>.json` with its error trace (including any
outstanding lint/validation issues).

## Outputs (per client)

```
report/<slug>/report-file-<DDMMYYYY>.html    # dated audit copy
report/<slug>/report-file-latest.html        # latest-pointer, overwritten each run
report/<slug>/status-<MMYYYY>.json           # per-client status manifest
```
