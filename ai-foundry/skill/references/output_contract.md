# Output contract

The generator must return a single downloadable HTML file only. The renderer/template own visual layout, responsive behavior, and navigation mechanics; do not recreate those rules in narrative prompts.

## File naming
Name the output file:

`AI_Ready_Leader_Pulse_YYYY-MM-DD_[ClientShortName].html`

Rules:
- Do not include the internal version in the filename.
- Use the client short name inferred from the uploaded workbook.
- Use the current report-generation date in `YYYY-MM-DD` format.
- Do not use prior-client names in the filename.

## Internal version metadata
The report surfaces the current skill/report version only in HTML source metadata so a user can inspect it without seeing it on the report page.

The current skill/report version is **1.11.17**. The report template should include near the top of `<head>`:

```html
<!-- ai-ready-leader-skill-version: 1.11.17 -->
<script id="ai-ready-leader-skill-metadata">
  window.AI_READY_LEADER_PULSE = Object.freeze({
    version: "1.11.17",
    name: "AI Ready Leader Pulse",
    outputFormat: "html",
    versionVisibility: "internal-devtools-only"
  });
</script>
```

See `references/developer_notes.md` for changelog and versioning policy.

## Upstream subgroup eligibility

Subgroup N eligibility is enforced upstream in the SQL/export process that creates the workbook. The skill should render the subgroup score rows provided in the workbook and should not apply an additional minimum-N filter unless the workbook contract changes. Limited-data copy must describe workbook comparison availability, not claim the renderer applied the threshold.


## Dual-benchmark report behavior

When the content model contains more than one benchmark view, render one HTML report with a sticky-navigation benchmark toggle. The default view is the workbook-supplied Overall Benchmark. The secondary view is the fixed High Engagement Benchmark derived from `references/benchmark_definitions.json`. Keep the toggle hidden until the navigation reaches its sticky, section-link-visible state.

Benchmark-dependent sections must render paired benchmark views and hide/show them with the toggle:
- Executive Narrative callouts
- Interpretive Storyline
- Benchmark Comparison chart and heading
- Underlying Leadership Signals
- Function, Job Level, and Region heatmaps

Shared sections must not duplicate by benchmark: Hero, AI-Ready Leader explainer, About the Data, Recommended Follow-up Opportunities, External Context Sources, and footer. The sticky-nav toggle is the sole persistent active-benchmark indicator; do not repeat active-benchmark badges in individual sections. Heatmap explanatory footnotes remain static. The Benchmark Comparison footnote keeps a fixed explanatory sentence and appends deterministic context for the selected benchmark. Benchmark-specific narratives must be standalone and must not assume the alternate benchmark view is shown. Interpret Structure and Balance as low-target constructs: stronger profile fit reflects alignment to a lower target, never more of the named construct. The Benchmark Comparison `How to read the scores` footnote must append deterministic context only for the selected benchmark, including approximate population scale and, for High Engagement, the Work Engagement selection/methodology note. Do not render a separate Benchmark Context block.

## Required sections and order
Every full report must contain these sections in this order:

1. Hero with unified header/navigation
2. AI-Ready Leader explainer
3. About the Data
4. Executive Narrative
5. Interpretive Storyline
6. Benchmark Comparison
7. Underlying Leadership Signals
8. Functional Patterns
9. Job Level Patterns
10. Regional Patterns
11. Recommended Follow-up Opportunities
12. External Context Sources, when URL-backed sources are provided
13. Footer

## Required behavior
- Every report must include all template-defined headings, narrative elements, cards, charts, heatmaps, footnotes, tooltips, legends, disclaimers, and source displays that apply to the available data.
- Do not omit a required section because it seems less relevant or repetitive. Use the limited-data behavior below when subgroup data is unavailable.
- The content model must pass `scripts/validate_content_model.py` before client-ready rendering. Render blocking may be bypassed only for development testing with `--allow-default-narrative`.
- The unified header/navigation is deterministic template behavior: logo, stacked identity, sticky behavior, hidden-to-visible section links, active-section highlighting, click-to-top logo behavior, responsive scrolling, and print hiding are handled by the HTML/CSS/JS template.

## Fixed AI-Ready Leader explainer
Render one simple report-style card after the Hero and before About the Data.

Required content:
- heading: `What is the AI-Ready Leader?`
- approved Success Profile description text
- `Learn More` button linking to `https://www.kornferry.com/institute/introducing-the-ai-ready-leader`
- no list of the six responsibility names

## About the Data
- Include the Data interpretation note as a concise bulleted note.
- When nonblank values are available from optional `ClientName`, include the client-records bullet; otherwise omit only that bullet.
- Display employee count as an approximate rounded-down figure when available, never as exact web-sourced headcount.

## Function, Level, and Region heatmap states
For each heatmap section:

- **Two or more usable subgroup score rows:** render the normal comparative headline, heatmap table, three interpretation cards, and the Interpretation Guide footnote.
- **Exactly one usable subgroup score row:** render the section with the deterministic limited-data headline, the single-row heatmap table, and one concise limited-comparison note. Do not render comparative interpretation cards or the Interpretation Guide.
- **Zero usable subgroup score rows:** keep the section visible with the deterministic limited-data headline, do not show an empty heatmap table, and render one concise data-coverage note.

The limited-data headlines and note copy are deterministic renderer behavior. They should explain the value that Function, Job Level, or Region cuts could provide without implying unsupported subgroup findings.

## Functional Focus Area
The Functional Patterns heatmap may show a vertical `Focus Area` pill when the Python cluster logic selects highlighted rows. Selection logic lives in `references/scoring_rules.md`; visual placement is deterministic template behavior.

## External context sources
If `external_context.sources` or `external_context.vetted_context_bullets` contains usable URL-backed entries, render a compact `External context sources` section near the bottom before the footer. Each source renders as a linked source/headline with a concise inline context/purpose note when available. Vetted bullet claims themselves do not render in this section. Raw URLs should not print as visible text.

## Footer and disclaimer
The full-width Korn Ferry footer must be present and use `© 2026 Korn Ferry`.

The footer must contain the required AI disclaimer exactly:

`This has been produced with help from AI.  Check for accuracy.  Korn Ferry is responsible for all deliverables to clients regardless of production method.`

## Source and reuse rules
- Use the uploaded workbook as the only source for client data, client scores, Overall Benchmark values/gaps, rankings, n sizes, demographics, and client names. Use `references/benchmark_definitions.json` as the only source for fixed High Engagement benchmark values; derive its gaps and benchmark-dependent visuals in Python.
- Do not reuse data, visuals, rankings, heatmaps, narrative insights, web context, or recommendations from prior clients.
- Do not use prior-client reports or development reference HTML as source material.
