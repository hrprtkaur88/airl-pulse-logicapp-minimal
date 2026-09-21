---
name: airl-pulse-report
description: generate client-ready Korn Ferry AI-Ready Leader HTML insight reports from uploaded assessment workbooks. Use when asked to create, update, validate, or template an AI-Ready Leader report using client data, benchmark gaps, demographic cuts, construct signals, external AI strategy context, AI-Ready Leader IP/reference materials, or KF Beautiful-aligned styling. Also use when the user asks for the repeatable workflow, guardrails, narrative prompts, source hierarchy, QA checks, or template logic behind these reports.
---

# AIRL Pulse Report

## Version and maintenance

Current skill/report version: **1.11.17**. Version history and versioning policy are maintained in `references/developer_notes.md`. This developer-note file is maintenance-only and is not source material for client report narrative generation.


Generate an HTML-only AI-Ready Leader client insight report from a workbook with `demographics` and `data` sheets.


## Dual-benchmark behavior

Build two benchmark views in every report. Treat workbook `BenchmarkPct` / `GapVsBenchmark` as the default **Overall Benchmark**. Derive the **High Engagement Benchmark** from `references/benchmark_definitions.json`; the client workbook does not need `Benchmark2Pct` or `GapVsBenchmark2`. The build step applies the fixed benchmark at Overall, responsibility, and construct grain and calculates `GapVsBenchmark2` deterministically for Overall, Function, Level, and Region rows. If legacy second-benchmark columns are present, the canonical bundled reference overwrites them.

Render both views in one HTML file with the sticky-navigation benchmark toggle. Benchmark-dependent sections switch values, charts, heatmaps, callouts, and benchmark-specific narrative fields. Shared sections such as Hero, AI-Ready Leader explainer, About the Data, Recommended Follow-up Opportunities, External Context Sources, and footer remain single-version. The Benchmark Comparison section includes deterministic context for both benchmark populations and methodologies.

Write benchmark-specific interpretive narrative in `benchmark_narratives.<benchmark_id>` when the selected comparison materially changes the story. Each view must read as a complete standalone report because a consultant may present only one benchmark. Treat the benchmark as evidence, not as the subject of the story: do not compare views, do not describe a benchmark as shifting or raising the question, and do not repeatedly use phrases such as `higher bar`, `aspiration gap`, or `stretch standard`. Name the selected benchmark only when needed to orient a specific comparison. Shared `narrative` fields may still provide common language. The sticky-nav toggle communicates the selected comparison; do not add repeated active-benchmark badges or dynamically rewrite explanatory footnotes.

## Required workflow

1. Read the uploaded workbook and validate it with `scripts/validate_workbook.py`.
2. Build a data content model with `scripts/build_content_model.py`.
3. Search the web for current client context: approximate global employee count and AI/digital strategy. Use official or reputable sources when possible. Record employee count as an approximated, rounded figure, not an exact headcount.
4. Use the reference files and source hierarchy to write or refine narrative fields in the content model.
5. Run `scripts/lint_narrative_labels.py` on the revised content model before rendering. If it flags label-led prose, missing required substance, weak external-source grounding, or other content-quality issues, rewrite the flagged narrative fields and rerun the lint until it passes.
6. Set `narrative_status` to `final` only after all required narrative fields are client-ready, then run `scripts/validate_content_model.py` and resolve any blocking issues.
7. Render the HTML with `scripts/render_report.py`. The renderer blocks non-final content models unless `--allow-default-narrative` is used for development testing only.
8. Run the QA checklist before returning the file.

Use `/mnt/data` for generated reports and return the HTML file link to the user.

## Clarification behavior

Do not ask clarifying questions unless required sheets or columns are missing, the client identity cannot be determined, or the workbook does not contain the data needed to render a required report element, such as no regional data for the Regional Patterns section. Make reasonable assumptions using the skill rules whenever the workbook contains enough data to proceed. If one demographic category is sparse or contains nulls, exclude null categories and continue when there is still usable data for the required element.


## Reference files

For every full report generation, use these files as the governing instructions and reference sources. For minor edits to an existing report, load only the files needed for the requested change while preserving everything else.

- `references/workbook_schema.md` for required workbook structure.
- `references/scoring_rules.md` for calculations, heatmap selection logic, definitions, rounding, and score-display rules.
- `references/benchmark_definitions.json` as the deterministic source of High Engagement benchmark metadata and fixed Overall/responsibility/construct values; Python consumes this file directly.
- `references/narrative_rules.md` for content-block writing rules, narrative quality standards, and section-level prompts.
- `references/source_context.md` for source hierarchy and how to use the bundled source materials.
- `references/construct_composite_definitions.md` for LLM-readable behavioral interpretation of responsibilities, constructs, strengths, watch areas, and narrative implications.
- `references/ai_ready_leader_thought_leadership.md` for Human + AI leadership framing and responsibility-level interpretation.
- `references/ai_ready_leader_client_positioning.md` for client-facing positioning and commercialization language.
- `references/ai_ready_leader_project_concept.md` for project purpose and output-design intent.
- `references/ai_ready_leader_seller_faq.md` for seller FAQ guardrails, profile differentiation, construct rationale, practical development guidance, and broader engagement pathways.
- `references/web_research_rules.md` for external client context research.
- `references/qa_checklist.md` before returning output.
- `references/output_contract.md` for filename, internal version metadata, required sections, deterministic output elements, and required footer/disclaimer text.
- `references/operator_playbook.md` when lint, validation, or rendering returns issue codes that require action routing before continuing.
- `references/visual_contracts.md` for maintenance-only visual QA after CSS/template changes; do not use it as narrative source material.
- `references/developer_notes.md` for maintenance notes, versioning policy, and changelog history only; do not use it as a report-generation narrative source.


## Guardrails

- Use only the uploaded client workbook for client scores, participant counts, demographics, and client names. Use `references/benchmark_definitions.json` as the authoritative source for the fixed High Engagement benchmark values; Python deterministically derives its gaps and benchmark-dependent displays.
- Subgroup eligibility thresholding, including the minimum N-size cut for reported subgroup cuts, is enforced upstream before the workbook reaches this skill. Do not add a second participant-count filter in the skill unless the workbook contract changes.
- Do not reuse prior-client data, narrative, visuals, rankings, heatmaps, web context, or recommendations.
- Do not use prior-client reports or development reference HTML as narrative source material.
- Do not imply statistical significance.
- Do not claim the assessed population represents the full organization.
- Do not describe the results as coming from a dedicated AI-Ready Leader diagnostic.
- Treat results as directional early-read signals.
- Treat the report as an AI readiness indicator, not an AI readiness index or definitive single score.
- Distinguish leadership readiness from AI fluency or technology readiness.
- Avoid em dashes.
- Avoid the word `spread`; use `gap`, `difference`, `relative advantage`, or similar language.
- Explain gaps as percentage-point differences to the benchmark.
- Keep output HTML-only unless the user explicitly requests another format.
- Include the KF footer disclaimer exactly as specified in `references/output_contract.md`.

## Script usage

Validate:

```bash
python scripts/validate_workbook.py /path/to/client_workbook.xlsx
```

Build content model:

```bash
python scripts/build_content_model.py /path/to/client_workbook.xlsx --out /mnt/data/content_model.json
```

Run narrative lint before rendering:

```bash
python scripts/lint_narrative_labels.py /mnt/data/content_model.json
```

If lint returns issues, use the issue codes and `references/operator_playbook.md` to route the fix, then rerun lint. Do not render a client-ready report until lint passes.

Finalize and validate the content model before rendering:

```bash
python scripts/validate_content_model.py /mnt/data/content_model.json
```

Set `narrative_status` to `final` only when required narrative fields are complete, source-grounded, and ready for client rendering. Use issue codes from validation to fix the right layer: rewrite narrative for `STYLE_*`, repair content-model fields for `CONTRACT_*`, and update sources for `SOURCE_*`. Use `--allow-draft` only for development checks.

Render report:

```bash
python scripts/render_report.py /mnt/data/content_model.json --out /mnt/data/report.html
```

Use `--allow-default-narrative` only for internal development/test renders. Do not use it for client-ready reports.

After web research, edit `content_model.json` to populate `external_context.employee_count`, `external_context.ai_strategy_summary`, and URL-backed `external_context.sources` before rendering. Store `external_context.employee_count` as a rounded approximate figure (for example, `93,000`, not `93,427`). Each external source used for company headcount or AI/digital context must include `title`, `url`, and a short `purpose` note. Optionally add `external_context.vetted_context_bullets` as an evidence ledger for specific external facts; each bullet should include `claim`, `source_title`, `source_url`, and `use`. Treat these bullets as factual grounding for synthesis, not as required wording or a limiter on consultant interpretation.

## Narrative generation approach

The scripts create a data-grounded draft model. ChatGPT must improve narrative text before rendering by applying `references/narrative_rules.md`, `references/source_context.md`, the AI-Ready Leader Markdown references, construct definitions, and current web research.

Before drafting final narrative, establish a concise insight spine from the workbook and current web context. Use it as a coherence anchor for the main story, not as a ceiling. Section-specific insights may extend beyond the spine when they are clearly supported, useful, and non-contradictory. If a high-value finding conflicts with the spine, reassess whether it is a nuance to explain, evidence that the spine should evolve, or too isolated to include. This remains a drafting discipline, not a required structured content-model artifact.

Narratives should synthesize four inputs:
1. the client's actual data pattern,
2. relevant responsibility/construct meaning,
3. client AI/digital strategy context when available,
4. the leadership implication or recommended action.



Draft narrative in this staging order: first identify labels and patterns internally, then translate labels into behavioral meaning, then run the narrative label lint. The final prose should not contain label lists, even when the analysis behind the prose used responsibility or construct names.

When interpreting heatmaps, explicitly scan for high-value counter-patterns before writing callouts or recommendations. Use them only when they sharpen the story or prevent an overbroad statement. Counter-patterns should temper or enrich the narrative, not add another required visual or extra callout.

Use definitions and source materials as interpretation context, not as text to copy. The final report should sound like a Korn Ferry consultant explaining the story behind the data to a senior client team. Do not treat script-generated default narrative as final copy. The fallback narrative in `scripts/airl_default_narratives.py` is placeholder scaffolding only and the renderer blocks client-ready output unless `narrative_status` is `final`. Before rendering a final report, rewrite narrative fields so they translate labels into behavioral meaning, Human + AI transformation implications, and client-specific action. Avoid label-led narrative that simply lists responsibility, composite, competency, trait, or driver names.

## Required structure and source rules

- Use `references/output_contract.md` for the required section order and deterministic output elements. Do not restate template-owned visual behavior in narrative prompts.
- Focus generative effort on client-specific narrative fields: hero copy, executive interpretation, storyline cards, heatmap callouts when comparative subgroup data exists, and follow-up recommendations.
- Recommended Follow-up Opportunities must be client-specific, data-specific, prescriptive, and connected to the client's AI strategy and observed readiness pattern.
- Do not include or rely on prior-client reference HTML in the generation workflow.

## Revision behavior

If the user asks for edits to an existing generated report, preserve everything else exactly as-is unless explicitly requested. For minor narrative edits, modify only the requested text areas and keep all data, visuals, layout, styling, filenames, and other narrative sections unchanged. Do not regenerate the full report unless the user asks for a rebuild or provides a new client workbook.

If the user uploads a new client workbook, treat it as a fresh report generation. Do not reuse prior-client data, visuals, rankings, heatmaps, narrative insights, web context, or recommendations. Generate all data visuals and narrative from the new workbook, reference materials, and current web context only.

