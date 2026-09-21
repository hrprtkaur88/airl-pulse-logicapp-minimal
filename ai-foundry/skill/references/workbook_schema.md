# Workbook schema

The user supplies one Excel workbook with exactly these two required sheets.

## Required sheet: `demographics`

Required columns:
- `CIQUltimateParentName`
- `AssmtKey`
- `CompletedYear`
- `CompletedDate`
- `Region`
- `FunctionName`
- `LevelName`
- `AssessmentType`

Rules:
- Use `CIQUltimateParentName` as the legal client name.
- Infer a common client name for report copy, but never change the data.
- `ClientName` is optional. When present with nonblank values, use trimmed distinct values as Korn Ferry client record names for the About the Data interpretation note.
- Exclude null, blank, `nan`, or `None` demographic values from chart categories.
- Show participant count, date range, year distribution, level distribution, regional mix, and assessment type.

## Required sheet: `data`

Required columns:
- `CutType`
- `CutName`
- `DataType`
- `KF4D_Code`
- `Construct`
- `CompositeName`
- `ParticipantCount`
- `TargetHitPct`
- `BenchmarkPct`
- `GapVsBenchmark`

Rules:
- `ClientName` is optional. If present with nonblank values on the data sheet, use it as the authoritative source for Korn Ferry client record names in the About the Data interpretation note. Trim whitespace, preserve the supplied text exactly, deduplicate, and alphabetize for display.
- `DataType = Overall` with `CutType = Overall` provides the authoritative `[Client] Overall` score, benchmark, and gap for the Benchmark Comparison overall bar when present.
- If `DataType = Overall` is absent, preserve backward compatibility by using the historical average of the six `DataType = Composite` / `CutType = Overall` rows for the Benchmark Comparison overall bar.
- `DataType = Composite` rows drive the six responsibility charts and heatmaps.
- `DataType = Construct` rows drive Underlying Leadership Signals.
- `CutType = Overall` gives overall composite and construct results.
- Heatmaps use `CutType = Function`, `Level`, and `Region`.
- Do not invent missing cut types or demographic categories.

### Fixed High Engagement benchmark

The client workbook does **not** need to provide a second benchmark. `scripts/build_content_model.py` loads the canonical fixed values from `references/benchmark_definitions.json`, applies them to every data row at the matching measurement grain, and calculates `GapVsBenchmark2 = TargetHitPct - Benchmark2Pct`.

Rules:
- `BenchmarkPct` / `GapVsBenchmark` remain the workbook-supplied Overall Benchmark comparison.
- The bundled High Engagement benchmark is the single source of truth for the second comparison.
- Use the same High Engagement Overall, responsibility, or construct value for every subgroup row at that measurement grain; subgroup-specific benchmark norms are not provided.
- Legacy `Benchmark2Pct` / `GapVsBenchmark2` workbook columns may be present during transition, but the build step overwrites them with the canonical reference values.
- Missing benchmark mappings are blocking build errors; do not silently substitute another construct or responsibility value.


## Hero client label
- Hero tag must use `CIQUltimateParentName` exactly as the legal client name: `AI-Ready Leader Insights | [CIQUltimateParentName]`.
- Use the inferred common client name only in narrative copy and filename where appropriate.


## Validation expectations

`validate_workbook.py` blocks or warns on common workbook risks before report generation:

- required sheets and columns missing
- no nonblank `CIQUltimateParentName`
- required numeric fields missing, nonnumeric, or outside expected ranges
- missing six `DataType = Composite` / `CutType = Overall` responsibility rows
- duplicate aggregate keys that could silently average or double-count rows
- `GapVsBenchmark` values materially inconsistent with `TargetHitPct - BenchmarkPct` beyond rounding tolerance

Resolve blocking validation errors before building the content model.
