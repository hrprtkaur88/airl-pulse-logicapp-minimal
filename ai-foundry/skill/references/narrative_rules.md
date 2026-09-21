# Narrative rules and prompt guidance

Use this file after the workbook content model is built and before final HTML rendering. The goal is to turn the data model into a coherent client story, not to restate scores, labels, or methodology.

## 1. Narrative purpose, voice, and measurement boundary

Write like a Korn Ferry consultant explaining the story behind the data to a senior client team.

The report should be:
- client-ready, polished, and commercially useful;
- specific to the uploaded workbook and current client context;
- insight-led rather than a data recap;
- grounded in Korn Ferry AI-Ready Leader IP;
- direct, concise, and free of generic consulting filler.

Avoid em dashes. Avoid the word `spread`; use `gap`, `difference`, `relative advantage`, or similar language.

### Measurement boundary
Scores reflect leadership tendencies, behavioral signals, and underlying competencies, traits, and drivers that may support AI-ready leadership. They are not direct proof that the client has successfully implemented, scaled, or achieved results from AI initiatives.

Use directional, indicative language where appropriate. Do not imply statistical significance, do not say the assessed population represents the full organization, and do not position the report as a definitive AI readiness index or standalone AI/technology maturity diagnostic.

Describe what the leadership pattern may enable, support, accelerate, or constrain. Do not claim the organization has already achieved the related business outcome because a score is high.

## 2. Source use and grounding

Use sources for interpretation, not for copying text.

Source ownership:
- The uploaded workbook is the only source for client data, client scores, Overall Benchmark values/gaps, n sizes, demographics, subgroup results, rankings, visuals, client names, and client-record names. `references/benchmark_definitions.json` is the only source for fixed High Engagement benchmark values; use Python-derived gaps from the content model for that view.
- `construct_composite_definitions.md` explains behavioral meaning of competencies, traits, drivers, composites, and responsibilities.
- `ai_ready_leader_thought_leadership.md` frames AI-Ready Leader IP and Human + AI leadership.
- `ai_ready_leader_client_positioning.md`, `ai_ready_leader_project_concept.md`, and `ai_ready_leader_seller_faq.md` guide client-facing positioning, commercialization, and follow-up implications.
- `web_research_rules.md` governs external research for approximate employee count and public AI/digital or company strategy context.

Use external context only to explain why the workbook pattern matters for this client. It must not alter workbook data or scoring. Company-specific facts used in narrative must be traceable to URL-backed `external_context.sources` or optional `external_context.vetted_context_bullets` with concise purpose/use notes. Treat vetted bullets as an evidence ledger, not as text to copy or a limit on interpretive synthesis.

Do not refer to the source-gathering process in client-facing narrative. Avoid phrases such as `public strategy context`, `external context`, `strategy context`, `web context`, `this research`, or `the source indicates`. Instead, name the concrete business condition or AI/digital priority directly.

Do not introduce unsourced specific claims such as financial amounts, country counts, named AI programs, named partnerships, product launches, or R&D spend unless the content model includes URL-backed source entries or vetted evidence bullets supporting those facts.

## 3. Required narrative substance

Every narrative element should answer: **So what does this mean for this client’s AI transformation?**

Use this interpretation chain:

`data pattern -> behavioral meaning -> AI transformation implication -> client-specific action`

Good narrative connects at least three of:
- the client’s actual data pattern;
- relevant responsibility or construct meaning;
- client AI/digital strategy or business context where available;
- the leadership implication;
- recommended action or commercialization opportunity.

Avoid generic phrases such as `deployment priorities`, `targeted enablement`, `leadership routines`, `AI adoption patterns`, `acceleration zones`, or `scale learning` unless tied to a specific group, score pattern, leadership behavior, business condition, or action.

## 4. Label interpretation rules

Use responsibility, composite, construct, competency, trait, and driver names internally to analyze the data. In prose, translate those labels into behavioral meaning and client implications.

Labels may appear in titles, card headers, chart labels, table rows, legends, tooltips, and an occasional essential anchor when the label is not visible nearby. Narrative text should not become a list of labels.

If a label already appears in the related title, card, chart, or table, the adjacent narrative should usually move directly to:
1. behavioral interpretation;
2. AI transformation implication;
3. client-specific consequence;
4. action or follow-up opportunity.

Do not write comma-separated or serial lists of responsibility, composite, competency, trait, driver, or construct names in narrative prose.

Bad:
> The strongest signals are Address Fears, Sustain the Vision, and Take Decisive Action.

Better:
> The strongest advantages point to leaders who may be comparatively ready to create confidence, hold attention on the future, and help teams keep learning as AI changes work.

Run `scripts/lint_narrative_labels.py` against the revised draft content model before setting `narrative_status` to `final`. If it flags label-led prose, rewrite the flagged fields and rerun the lint.

## 4.1 Dual-benchmark narrative independence

When a report contains more than one benchmark view, write each benchmark-specific narrative as a complete standalone client story. A consultant may present only one view. The prose must remain natural and complete without assuming the reader has seen, or will see, the alternate comparison.

Treat the selected benchmark as **evidence**, not as the narrative subject. The data story should lead with the observed leadership pattern, behavioral meaning, AI transformation implication, and action. Benchmark wording is supporting orientation only.

- Do not compare the two benchmark views inside client-facing prose.
- Do not refer to `the other benchmark`, `the overall view`, a benchmark switch, or a prior comparison.
- Do not call the High Engagement Benchmark a `stretch benchmark`, `stretch standard`, `higher bar`, `higher aspiration`, or `aspiration gap`.
- Do not describe a benchmark as shifting, raising, changing, or reframing the question.
- Avoid benchmark-led headings. Headings should state the leadership finding directly.
- Name the selected benchmark only when the source of a specific comparison genuinely matters, typically no more than once in a major section. After orientation, interpret the pattern directly.
- Let benchmark-specific scores, strengths, constraints, and implications change the story where the evidence changes; do not manufacture different prose when the practical implication is materially the same.
- Keep examples in these rules generic. Never insert an actual client name into narrative-rule examples.

Avoid:
> The higher benchmark shifts the question from readiness to consistency.

Prefer:
> Readiness is visible, but consistency remains the enterprise challenge.

Avoid:
> Under the stretch standard, decisive action becomes the critical aspiration gap.

Prefer:
> Decisive action is the clearest constraint on converting readiness into repeatable execution.

Acceptable when orientation is needed:
> Relative to the High Engagement Benchmark, this responsibility remains the closest point of strength.


## 5. Insight spine and consistency

Before drafting, establish a concise insight spine from the workbook and current web context. This is a drafting discipline, not a required structured content-model artifact.

The spine should identify:
- the overall benchmark pattern;
- the strongest relative responsibility signal;
- the lowest relative responsibility signal;
- the most important behavioral meaning;
- the most relevant function, level, and region patterns;
- the main implication for client follow-up.

Narrative wording may vary across runs, but the core meaning should remain consistent for the same workbook and current context. Section-specific insights may add nuance when they are supported and useful, but they should not contradict the main storyline without explanation.

For Hero, Executive Narrative, Interpretive Storyline, and Recommended Follow-up Opportunities, consider more than one framing internally and choose the strongest one based on evidence fit, client relevance, actionability, and alignment with AI-Ready Leader IP.

## 6. Section and element guidance

### Hero
The hero headline and subheading must state the main client implication. They must not describe the report, sample, analysis process, or methodology.

The hero subheading must not include participant counts, sample sizes, score values, or assessment-methodology language. It should state the client implication directly rather than describing the report, sample, analysis process, or directional nature of the evidence. Common failure patterns are enforced by the lint and content-model validator.

Use the subheading to explain why the pattern matters for AI transformation, leadership behavior, or scalable adoption.

Better pattern:
> The pattern points to a leadership population with enough trust and learning capacity to support AI-enabled change, but scaling value will depend on turning local momentum into disciplined enterprise routines.

### AI-Ready Leader explainer
Render the fixed explainer text approved in the template. It should introduce the AI-Ready Leader Success Profile as Korn Ferry IP, not explain the report methodology or the data realignment process. Do not list all six responsibility names in this explainer.

### About the Data
Use the approved bulleted Data interpretation note. Keep it factual and methodological. This is where directional language, participant counts, employee population, client-record coverage, assessment timing, and confidence guidance belong.

### Executive Narrative
Always include two concise paragraphs and a Commercial Implication callout.

Paragraph 1:
- Lead with the leadership implication, not a score recap.
- Interpret the overall benchmark pattern in business language.
- Use no more than one concise quantitative anchor in the full executive narrative unless a true contradiction cannot be explained without a second number.
- Prefer benchmark direction over multiple point values.
- Do not use participant count as the executive data anchor unless sample size materially changes the confidence story.
- Do not stack multiple responsibility gaps or construct values.
- Do not list top responsibilities or constructs by name when visible elsewhere.

Paragraph 2:
- Connect client AI/digital or business context to the assessment pattern.
- State the concrete business condition directly rather than referencing `strategy context` or `external context`.
- Explain the leadership tension or opportunity created by the data.

Commercial Implication:
- State what the client can do with the result.
- Connect at least two of: top relative responsibility signal, lowest relative responsibility signal, heatmap pattern, external strategy, construct signals.
- Avoid generic calls to `targeted enablement` unless you say who needs it and why.

Before rendering, fix malformed punctuation such as `.,` or `,.`.

### Largest Advantage / Relative Strength card
Use the deterministic card label supplied in `metrics.largest_advantage_label`.

- If the highest responsibility gap is above benchmark, the label is `Largest Advantage`.
- If the highest responsibility gap is zero or below benchmark, the label is `Relative Strength`.

The card title names the responsibility; the body should not open by repeating the title label. Explain the behavioral meaning, why it matters for Human + AI transformation, what the client can do with it, and what risk remains if it is not connected to enterprise priorities.

When the label is `Relative Strength`, describe the strongest available starting point. Do not imply that it is an above-benchmark advantage.

### Watch Area card
The card title names the responsibility; the body should not open by repeating the title label.

Check the displayed gap:
- If the lowest responsibility gap is negative, frame it as a potential scaling constraint or risk to manage.
- If the lowest responsibility gap is still positive, frame it as the lowest relative signal in an otherwise above-benchmark pattern, not as a deficit, weakness, or below-benchmark result.

Explain how the watch area interacts with the relative strength or advantage and what the client should reinforce.

### Benchmark Comparison
The Benchmark Comparison heading is deterministic and generated by `scripts/airl_view_model.py`; write or refine the body narrative only.

Always render the benchmark chart and dynamic section heading. The heading must match the client’s actual data pattern.

Only say the client `outperforms the benchmark` when the average benchmark gap is meaningfully positive. Use balanced language when results are near benchmark or below benchmark. Never describe a negative signed benchmark gap as above benchmark, or a positive signed benchmark gap as below benchmark.

The section lead should be a short interpretive paragraph, not a large narrative box. It should explain how to read the benchmark comparison without repeating chart labels.

### Interpretive Storyline
Always render this section. It should explain the story behind the data, not repeat the Executive Narrative.

Structure:
- two top insight cards carrying the main strategic interpretation;
- four expandable cards adding nuance around relative strengths, watch areas, construct signals, and subgroup patterns.

The top two cards should be the most impactful. Each card should be specific enough to anchor a client discussion.

### Underlying Leadership Signals
Interpret construct-level differentiators and watchpoints without relisting table labels. Explain what the construct pattern suggests behaviorally, how it may affect AI transformation, and what leadership work it points toward.

#### Low-target construct polarity
`Structure` and `Balance` are low-target constructs in the AI-Ready Leader Success Profile. A stronger profile-fit result means greater alignment to the lower target, not greater preference for the named construct. For Structure, translate stronger fit as lower reliance on routine/predictability and greater comfort with ambiguity; for Balance, translate stronger fit as greater tolerance for sustained transformation intensity without implying that overwork or poor wellbeing is desirable. Never describe a positive AIRL result as `high Structure`, `more Structure`, `enough Structure`, `high Balance`, or `more Balance`. Use the behavioral meaning from `references/construct_composite_definitions.md`.

### Function, Level, and Region heatmaps
For sections with two or more usable subgroup score rows:
- render the heatmap table;
- write three interpretation cards;
- include the Interpretation Guide footnote.

For exactly one usable subgroup score row, keep the single-row heatmap visible and rely on the renderer's deterministic limited-data headline and note. For zero usable subgroup score rows, keep the section visible without an empty heatmap table and rely on the renderer's deterministic data-coverage note.

Heatmap interpretation cards should explain why group patterns matter for AI transformation. Do not merely identify which group is high or low. Scan for meaningful counter-patterns before drafting: a lower-overall group may still have a storyline-critical strength, and a higher-overall group may still have a storyline-critical constraint.

Use counter-patterns only when they change the action logic, prevent overgeneralization, or sharpen the client story. Do not add extra cards mechanically.

Interpretation Guide footnotes should appear only for heatmap sections with two or more usable subgroup rows. Population and regional guides must include the small-n caution: `Small n sizes should be used directionally, not as definitive population comparisons.`

### Recommended Follow-up Opportunities

For dual-benchmark reports, keep the four recommended follow-up opportunities shared across benchmark views. Benchmark-specific sections may change interpretation and emphasis, but the report should present one stable action agenda unless the user explicitly requests separate recommendation sets.

Render four recommendations. Each card should be prescriptive and client-specific.

Each card should answer:
- What should the client do next?
- Which data pattern supports it?
- Why does it matter for AI-ready leadership or AI transformation?
- Where could Korn Ferry help?

Each card should connect at least two of: external AI strategy, relative strength or advantage, watch area, function/level/region pattern, construct differentiators/watchpoints, and commercial outcome.

### External Context Sources
The bottom External context sources section is for source transparency only. Source capture is governed by `references/web_research_rules.md`; display is handled by the renderer.

## 7. Final gates before rendering

Before rendering a client-ready report:
1. Rewrite script-generated scaffolding into final client-ready narrative.
2. Run `scripts/lint_narrative_labels.py` and fix any flagged issues.
3. Set `narrative_status` to `final` only after lint passes and the narrative is complete.
4. Run `scripts/validate_content_model.py`.
5. Fix any flagged issues and rerun the checks.

The linter and validator are hard gates for client-ready output. The renderer’s `--allow-default-narrative` flag is for development/testing only.
