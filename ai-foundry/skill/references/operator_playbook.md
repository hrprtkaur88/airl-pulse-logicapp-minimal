# AI operator playbook

Use this file when a validation, lint, or render step returns issues. It is for the AI instance executing the skill, not for client-facing report narrative.

## Principle

Treat issue codes as action-routing signals. Do not render a client-ready report until lint and final content validation pass, unless explicitly creating a development smoke test with `--allow-default-narrative`.

## Normal execution loop

1. Validate the workbook.
2. Build the content model.
3. Add rounded external context and URL-backed sources when public AI/digital context is used.
4. Draft or refine all narrative fields.
5. Run narrative lint.
6. Fix all returned issues by code/action and rerun lint.
7. Set `narrative_status` to `final` only after the narrative is client-ready.
8. Run final content-model validation.
9. Render the report.
10. Run the QA checklist before returning the HTML.

## Issue-code routing

| Code pattern | Meaning | AI action |
|---|---|---|
| `STYLE_*` | Narrative quality or phrasing issue | Rewrite the flagged narrative field. Do not rebuild data unless the message points to an impossible data claim. |
| `CONTRACT_*` | Required content-model structure or deterministic contract issue | Populate the missing field, fix the content model, or rebuild from the workbook if the deterministic model is incomplete. |
| `SOURCE_*` | External context/source grounding issue | Add URL-backed source metadata, remove unsupported company-specific external claims, or revise external context. |
| `RENDER_*` | Client-ready render gate issue | Do not render final output. Complete narrative/validation first, then rerun validation. |
| `PLACEHOLDER_*` | Development placeholder leaked into final path | Rewrite the placeholder text. Never return this as client-ready output. |
| `VALIDATION_GENERAL` | Unclassified validation issue | Read the message literally, repair the flagged field or model path, and rerun the same command. |

## Common fixes

- `STYLE_LABEL_LED`: Replace label lists with behavioral interpretation and the Human + AI implication. Do not simply delete labels if the sentence still reads like a data readout.
- `STYLE_SIGNED_GAP_CONTRADICTION`: Correct the direction of benchmark language. Negative gaps are below benchmark; positive gaps are above benchmark.
- `SOURCE_MISSING_URL`: Add at least one URL-backed `external_context.sources` item or vetted evidence bullet, or remove the AI strategy summary.
- `SOURCE_MISSING_METADATA`: Add `title` and `purpose` to each URL-backed source.
- `SOURCE_INVALID_URL`: Replace malformed source URLs with valid `http://` or `https://` links; a plain domain string does not count as URL-backed evidence.
- `CONTRACT_FOLLOW_UP_COUNT`: Provide exactly four follow-up recommendations.
- `RENDER_NARRATIVE_NOT_FINAL`: Continue drafting and QA. Set `narrative_status` to `final` only when the full report is ready for client rendering.

## When to ask the user

Ask only when the workbook lacks required sheets/columns, the client identity cannot be determined, or a required report element cannot be produced from available data. Otherwise, fix issues using the workbook, references, and public web context.
