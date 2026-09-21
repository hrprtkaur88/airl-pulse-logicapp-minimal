# Web research rules

Use web research for current client context because it changes over time.

Required research items:
- current approximate global employee count
- current AI strategy, digital transformation strategy, AI partnerships, or AI investments
- relevant major platforms, programs, or business priorities tied to AI or digital transformation

Source quality:
- Prefer official company pages, annual reports, investor materials, and major reputable business/technology news.
- Record every external source used in `external_context.sources` with a concise source title, URL, and purpose (`headcount`, `AI/digital strategy`, or `company context`). URLs are required for external context source entries. For specific company facts that may be reused in narrative synthesis, optionally add `external_context.vetted_context_bullets` with `claim`, `source_title`, `source_url`, and `use`. Display formatting is owned by `references/output_contract.md` and the renderer.
- If reliable context cannot be found, say so and keep the narrative based on uploaded data only.

Use in report:
- Header Data Interpretation note: include participant count out of approximately rounded global employee count when reliable.
- Executive Narrative: connect AI strategy context to the observed readiness pattern.
- Recommended Follow-up Opportunities: make client-specific recommendations based on external strategy and data patterns.


Source selection for employee counts:
- Prefer the most recent reliable source.
- Prefer official company annual reports, 10-K/20-F filings, integrated reports, investor disclosures, corporate fact sheets, or official company pages over third-party aggregators.
- If multiple reliable sources differ, use the most recent official company or investor source. If no official current source exists, use the most recent reputable third-party source and phrase the count as approximate.
- Always round down within reason and never display exact headcount.

## Employee count rounding

Employee count must be approximate and rounded down for client-facing copy. Do not show exact headcounts from web sources in the report, even if an exact figure is available.

Rounding guidance:
- Under 1,000 employees: round down to the nearest 50 or 100.
- 1,000 to 9,999 employees: round down to the nearest 500 or 1,000.
- 10,000 to 99,999 employees: round down to the nearest 1,000.
- 100,000+ employees: round down to the nearest 5,000 or 10,000.

When a source says `approximately 93,371 employees`, display `approximately 93,000 employees`. When a source says `104,913 employees`, display `approximately 100,000 employees` or `approximately 104,000 employees` depending on the selected rounding base, but never round up.

Use phrasing such as `approximately 93,000 employees globally` or `roughly 120,000 employees globally`. The Data Interpretation note should never display a more precise number than the rounded-down approximate figure.

Guardrails:
- Do not imply causality between assessment results and public AI strategy.
- Do not use outdated or uncertain data as definitive.
- Do not overstate readiness beyond the assessed population.


## Industry context

Use industry-specific AI implications as a light interpretive layer only when grounded in the company's sector or researched company context. Prefer company-specific strategy language over generic industry commentary. Do not infer causal links between public AI strategy and assessment results.


## Source capture requirements

Whenever web context is used for employee count, AI/digital strategy, company-specific business context, or industry-specific AI implications, add a URL-backed source object to `content_model.external_context.sources` with:

- `title`: source/headline displayed in the bottom External context sources section
- `url`: link target; required for every source used
- `purpose`: concise inline note describing what context was used from the source

Optionally add `content_model.external_context.vetted_context_bullets` when you identify specific company facts that may anchor narrative synthesis. Each bullet should include:

- `claim`: concise factual statement to use as evidence, not report copy
- `source_title`: source/headline supporting the claim
- `source_url`: URL supporting the claim
- `use`: how the claim may be used, such as `AI strategy evidence`, `headcount evidence`, or `company context`

Do not put raw URLs in narrative text boxes. Do not introduce specific external facts, such as revenue, R&D spend, country counts, named partnerships, or named AI programs, unless those facts are supported by the captured sources or vetted evidence bullets.
