# Source context and hierarchy

Use the reference files with a clear source hierarchy. Do not treat all sources equally.

## Source usage

### `references/construct_composite_definitions.md`
Use this as the primary LLM-readable behavioral interpretation source. It translates construct/composite definitions into responsibility-level narrative guidance, including how to interpret each AI-Ready Leader responsibility as a strength or watch area and how to use underlying constructs in narrative insights.

Use this file especially for:
- Executive Narrative
- Largest Advantage
- Watch Area
- Interpretive Storyline
- Underlying Leadership Signals
- Heatmap takeaways
- Recommended Follow-up Opportunities

Definitions should shape interpretation, not be copied directly into the report. Use the guidance to explain what the result means for AI transformation, leadership behavior, deployment risk, and follow-up action.

### `references/ai_ready_leader_thought_leadership.md`
Use this as the primary LLM-readable thought-leadership source for what it means to be an AI-Ready Leader. It explains the six responsibilities, Human + AI leadership context, and why leaders are the bridge between unrealized AI value and well-orchestrated impact. Use it to guide conceptual framing, leadership implications, and responsibility-level interpretation.

### `references/ai_ready_leader_client_positioning.md`
Use this as the primary LLM-readable commercialization and client-facing positioning source. It explains why leadership readiness is the bottleneck to scaled AI value, how to frame the executive problem, and how to turn results into senior-stakeholder follow-up conversations. Use it especially for Executive Narrative, Commercial Implication, Interpretive Storyline, and Recommended Follow-up Opportunities.

### `references/ai_ready_leader_project_concept.md`
Use this as the primary LLM-readable project-purpose and output-design source. It explains the report's purpose: combine client AI Ready Leader data with Korn Ferry benchmarks, translate findings into commercially relevant insight, and equip client teams with targeted follow-up opportunities.

### `references/ai_ready_leader_seller_faq.md`
Use this as the primary LLM-readable seller FAQ and IP-deepening source. It provides business-case language, profile differentiation, AI readiness indicator guardrails, construct rationale, four-phase maturity framing, and practical development guidance by responsibility.

Use this file especially for:
- differentiating leadership readiness from AI fluency or technology readiness
- writing stronger Recommended Follow-up Opportunities
- sharpening executive and commercial implications
- explaining construct signals with behavioral precision
- framing the report as an entry point to broader Human + AI transformation work

## Source hierarchy when sources overlap

1. The uploaded client workbook governs client scores, Overall Benchmark values/gaps, n sizes, demographics, and client subgroup results. `references/benchmark_definitions.json` governs fixed High Engagement benchmark values; Python deterministically derives High Engagement gaps and benchmark-dependent displays from those two sources.
2. `references/construct_composite_definitions.md` governs behavioral interpretation of responsibility and construct results.
3. `references/ai_ready_leader_thought_leadership.md` governs conceptual framing and responsibility definitions.
4. `references/ai_ready_leader_seller_faq.md` governs seller FAQ guardrails, profile differentiation, construct rationale, practical development guidance, and broader engagement pathways.
5. `references/ai_ready_leader_client_positioning.md` governs client-facing language, commercialization framing, and recommended action tone.
6. `references/ai_ready_leader_project_concept.md` governs report purpose and output design.
7. Web research is used only for current client context, employee count, and external AI strategy, and must be sourced or summarized cautiously.

## Narrative source rule
Always synthesize across sources. Do not paste definitions or FAQ text directly into the report. The final report should sound like a client-ready Korn Ferry consultant interpretation, not an excerpt from source documentation.


## Maintenance-only files
`references/developer_notes.md` is for human maintainers and future skill-development work. It contains maintenance notes, versioning policy, and changelog history. It is not source material for client report narrative generation and should not be cited, summarized, or used to shape client-facing interpretation when running a report.
