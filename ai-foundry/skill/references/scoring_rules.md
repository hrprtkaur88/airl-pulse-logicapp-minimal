# Scoring and display rules

## Six responsibilities
Use this order in all charts:
1. Sustain the Vision
2. Take Decisive Action
3. Scale for Impact
4. Don't Stop at Success
5. Champion Learning and Unlearning
6. Address Fears

## Display definitions
- Sustain the Vision: Anchor teams around a compelling AI-based vision, maintain focus, and remain committed.
- Take Decisive Action: Act with deliberate urgency. Balance the need to perfect, progress, pause and stop.
- Scale for Impact: Prioritize efforts that maximize scale and impact over fragmented experiments.
- Don't Stop at Success: Avoid complacency and foster a culture of continuous iteration and alternative thinking.
- Champion Learning and Unlearning: Spark a mindset of rapid learning and unlearning, and encourage a rethink of long-held habits.
- Address Fears: Address fears around AI's impact on jobs with integrity and authenticity.

## Metrics
- `TargetHitPct` is the client score shown as a percentage.
- `BenchmarkPct` is the benchmark target-hit percentage.
- `GapVsBenchmark` is a percentage-point difference between client and benchmark.
- `Benchmark2Pct` is the fixed High Engagement benchmark value loaded from `references/benchmark_definitions.json`; it is not required from the client workbook.
- `GapVsBenchmark2` is calculated in Python as `TargetHitPct - Benchmark2Pct`. The same fixed Overall/responsibility/construct benchmark is applied to all subgroup cuts at the matching measurement grain.
- For the Benchmark Comparison `[Client] Overall` bar, use the single `DataType = Overall` / `CutType = Overall` row when present. Use its `TargetHitPct`, `BenchmarkPct`, and `GapVsBenchmark` values directly.
- If the workbook does not include a `DataType = Overall` / `CutType = Overall` row, use the historical fallback: average the six `DataType = Composite` / `CutType = Overall` responsibility rows.
- Always call gaps `percentage-point gaps`, `gap to the benchmark`, `difference to the benchmark`, or `relative advantage`.
- Avoid the word `spread`.

## Heatmaps
- Sort each heatmap from lowest to highest average gap.
- Add an `Overall Gap` column showing each row's average gap across six responsibilities.
- Round visible heatmap values to no decimals.
- Base heatmap shading on the same rounded integer value shown in the cell, not the unrounded source value. If a negative number rounds to zero, show `0`, not `-0`, and shade the cell true neutral gray.
- Use a balanced absolute diverging heatmap scale for rounded gaps: `<= -15` strong red, `-12` to `-14` dark red, `-9` to `-11` medium red, `-6` to `-8` light red, `-3` to `-5` very light red, `-1` to `-2` warm red-gray, `0` true neutral, `+1` to `+2` cool green-gray, `+3` to `+5` very light green, `+6` to `+8` light green, `+9` to `+11` medium green, `+12` to `+14` dark green, and `>= +15` strong green.
- Keep the scale absolute across reports rather than report-relative so a given gap has the same visual meaning even when a workbook's gap range is narrow.
- Tooltips should show client score and gap to benchmark with one decimal precision.
- Highlight the lowest-opportunity cluster in the Function heatmap and label it `Focus Area`. Use baseline highlight counts of 0 rows for 1 group, 1 row for 2-3 groups, 2 rows for 4-5 groups, and 3 rows for 6+ groups.
- Adjust Function heatmap highlighting based on the gap distribution: reduce highlights when all groups are strongly above benchmark and the lowest row is clearly isolated from the next cluster; expand highlights up to 5-6 rows when many adjacent groups are materially below benchmark; treat approximately 5 percentage points as a meaningful cluster break in mixed/below-benchmark patterns and approximately 8 points as a clear break in strongly above-benchmark patterns.
- Include exact rounded ties at the highlight boundary only when doing so does not visually over-highlight a small or medium table; never highlight more than about half of the function groups.
- Include `n=` after the row name.

## Demographics
- Exclude null demographic categories from pie charts and legends.
- If a category percentage is below 1%, display `<1%`.
- Use a two-column legend for pie charts with 3+ categories; use one column for 2 categories.

## Missing subgroup score rows
Subgroup display states are owned by `references/output_contract.md`. Use workbook demographics, not web research, to decide regional limited-data context. Do not infer subgroup strengths, gaps, acceleration zones, or enablement priorities unless there are at least two subgroup score rows to compare.

## Advantage and watch-area labels

The highest responsibility gap drives the executive card traditionally called Largest Advantage. Use the deterministic label in the content model:

- `Largest Advantage` when the highest responsibility gap is greater than 0.
- `Relative Strength` when the highest responsibility gap is 0 or below 0.

When `Relative Strength` is used, narrative must describe the strongest available starting point without implying above-benchmark advantage. For the Watch Area card, if the lowest responsibility gap is still positive, narrative must acknowledge it as the lowest relative signal in an above-benchmark pattern rather than a below-benchmark weakness.
