# Visual contracts for AIRL Pulse Report

This file is maintenance-only guidance for future skill development and regression review. It is not source material for client-facing narrative generation.

## Purpose

Use this checklist when changing `assets/report_template.html`, CSS emitted by `scripts/render_report.py`, chart helpers, or any renderer-owned HTML classes. The goal is to protect known fragile visual expectations without turning the stylesheet into a screenshot-driven redesign process.

## Known fragile visual contracts

- About-the-Data Coverage card uses a single-line `Coverage` title, dark forest metric values, muted labels, and visible spacing between participant count, earliest assessment, and latest assessment.
- Demographic pie legend labels, including Region labels, render at 11.5px through the shared About-the-Data legend rule.
- About-the-Data interpretation note keeps compact list rhythm with visible spacing between bullets.
- AI-Ready Leader explainer body copy renders at 16px and the `Learn More` CTA uses the dark forest pill treatment.
- Benchmark Comparison lead/body copy renders at 16px.
- Heatmap table headers keep `Population` left-aligned and center-align all score/responsibility headers.
- Level heatmap kicker reads `Job Level patterns`; functional and regional heatmap kickers remain specific to those cuts.
- Recommended Follow-up Opportunities uses a dark-section palette: light mint kicker, soft mint-white lede/body copy, white action-card titles, and translucent action-card panels.
- External Context Sources uses compact body text and Korn Ferry forest-colored links, not default browser link blue.

## Maintenance rule

Prefer fixing these contracts in the owning CSS section or renderer helper. Do not add late patch overrides unless the owning section cannot be changed safely. Treat visible differences as regressions unless explicitly accepted by the project owner.

- Volume by Year and Level Distribution row labels and values should render at 11.5px; chart card headings remain 12px.

- Level Distribution keeps labels left-aligned while placing bars close to the label column; do not right-align labels or move count values to bar ends.
- Region Mix and Assessment Type legends use the simple inline legend treatment; do not force percentage alignment or stretch legend rows to the card edge. Keep the Assessment Type legend left-aligned while the pie remains centered.

## Dual-benchmark navigation and heatmaps

- Place the benchmark control inside the desktop sticky navigation row and align its right edge to the report-content rail.
- Keep the compact `Benchmark` label above the recessed Overall/High Engagement track, but position the label independently so the vertical centers of the benchmark buttons and section-navigation pills align exactly.
- Keep benchmark buttons slightly smaller than the section-navigation pills and visually distinct through the stronger mint active state; benchmark label and button text use the same 12px size as section-navigation text.
- Do not add a recessed background behind the section-navigation links.
- Reveal the benchmark control only when the sticky navigation links are active; hide it for print.
- At constrained widths, allow the section-link row to scroll and move the benchmark control to a clean row below rather than allowing overlap.
- Do not render active-benchmark badges inside report sections.
- Keep benchmark and heatmap explanatory footnotes static in wording and typography.
- Keep Recommended Follow-up Opportunities shared across benchmark views.
- Keep benchmark methodology inside the existing Benchmark Comparison `How to read the scores` footnote. Show only the selected benchmark context in the visible benchmark view; do not render a separate Benchmark Context block. When High Engagement is selected, include its concise aspirational-comparison rationale plus the Work Engagement proxy explanation.
- Anchor the functional Focus Area pill to the visible function heatmap table wrapper. Recalculate its vertical span after benchmark visibility changes; both views should occupy the same horizontal position when row structure matches.

## Underlying Leadership Signals score-reading note

- Use one fixed, benchmark-independent sentence; do not inject the client name or benchmark display label.
- Render the note at 12px with compact 1.4 line-height.

## About-the-Data responsive reflow

- Keep the five demographic cards in the canonical source order: Coverage, Assessment Volume by Year, Level Distribution, Regional Mix, Assessment Type.
- At medium widths, reflow to two columns and allow Level Distribution to span the row so labels and bars remain readable.
- At narrow widths, stack all cards in one column.
- Never preserve the five-column desktop grid when it causes horizontal overflow or clipped cards.

- The sticky navigation must reflow before the full `High Engagement` benchmark label can clip; desktop compression begins by 1500px and the benchmark control moves to its lower row by 1180px.
