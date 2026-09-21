# QA checklist

Use this checklist after workbook validation, narrative linting, content-model validation, and HTML rendering. Automated gates must pass before client-ready delivery; manual checks focus on coherence, support, and visible quality.

## Automated gates that must pass

1. Workbook validation:

```bash
python scripts/validate_workbook.py /path/to/client_workbook.xlsx
```

2. Narrative lint:

```bash
python scripts/lint_narrative_labels.py /mnt/data/content_model.json
```

3. Final content-model validation:

```bash
python scripts/validate_content_model.py /mnt/data/content_model.json
```

4. Render without development bypass flags:

```bash
python scripts/render_report.py /mnt/data/content_model.json --out /mnt/data/report.html
```

Do not use `--allow-default-narrative` for client-ready output.

## Manual data and source checks

- Workbook values drive client scores, Overall Benchmark values/gaps, n sizes, demographics, subgroup results, rankings, and client names. The fixed High Engagement benchmark comes only from `references/benchmark_definitions.json`, with gaps calculated in Python.
- No prior-client data, visuals, rankings, narratives, or web context appear in the report.
- Approximate employee count is rounded down and not presented as an exact headcount.
- Company-specific external facts used in prose are supported by URL-backed `external_context.sources` with concise purpose notes.
- External context sources render near the bottom with linked titles and inline purpose notes, not visible raw URLs.

## Manual narrative quality checks

- Hero headline and subheading state the client implication directly and do not describe the report, sample, readout, or methodology.
- Executive Narrative leads with insight, not a score recap, and does not stack multiple numeric anchors.
- Largest Advantage / Relative Strength and Watch Area card bodies interpret the visible title responsibility rather than repeating it.
- If the highest responsibility gap is zero or negative, the card label and prose use `Relative Strength` and do not imply above-benchmark advantage.
- If the lowest responsibility gap is still positive, Watch Area prose frames it as the lowest relative signal, not as a deficit.
- Narrative translates visible labels into behavioral meaning, AI transformation implication, and client-specific action.
- Narrative avoids generic consulting phrases unless tied to a specific client data pattern or business implication.
- Recommended Follow-up Opportunities include exactly four client-specific recommendations.

## Manual visual/output checks

- All required sections in `references/output_contract.md` appear in the correct order.
- Header/navigation, report sections, cards, footnotes, legends, and heatmaps do not overflow or visually collide at desktop, medium, or narrow widths.
- Function, Level, and Region sections follow the limited-data states defined in `references/output_contract.md`.
- Functional heatmap Focus Area, when present, follows the Python selection logic and renders without overlapping table labels.
- Data interpretation note includes assessed participant count and approximate global employee population when available.
- If `ClientName` values are available, the client-records bullet lists distinct trimmed names alphabetically and preserves supplied capitalization/punctuation.
- Client-records text does not replace the parent company name, short name, hero label, report filename, or other client references.
- Footer includes `© 2026 Korn Ferry` and the required AI disclaimer exactly.
- Final output is HTML only unless the user explicitly requested another format.
