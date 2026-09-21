#!/usr/bin/env python3
"""Benchmark configuration, fixed-reference loading, and view-model helpers."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pandas as pd

from airl_constants import normalize_responsibility_name

DEFAULT_BENCHMARK_ID = "overall"
SECONDARY_BENCHMARK_ID = "high_engagement"
REFERENCE_PATH = Path(__file__).resolve().parents[1] / "references" / "benchmark_definitions.json"


def load_benchmark_definitions(path: str | Path | None = None) -> dict:
    reference = Path(path) if path else REFERENCE_PATH
    if not reference.exists():
        raise FileNotFoundError(f"Benchmark definition reference not found: {reference}")
    return json.loads(reference.read_text(encoding="utf-8"))


def benchmark_configs(path: str | Path | None = None) -> list[dict]:
    definitions = load_benchmark_definitions(path)
    metadata = definitions.get("benchmarks", {})
    overall_meta = metadata.get(DEFAULT_BENCHMARK_ID, {})
    high_meta = metadata.get(SECONDARY_BENCHMARK_ID, {})
    return [
        {
            "id": DEFAULT_BENCHMARK_ID,
            "label": overall_meta.get("label", "Overall Benchmark"),
            "short_label": overall_meta.get("short_label", "Overall"),
            "pct_column": "BenchmarkPct",
            "gap_column": "GapVsBenchmark",
            "description": overall_meta.get("population_description", "Overall AI-Ready Leader benchmark comparison."),
            "methodology_note": overall_meta.get("methodology_note", ""),
            "footnote_context": overall_meta.get("footnote_context", ""),
            "participant_count_approx": overall_meta.get("participant_count_approx"),
            "organization_count_approx": overall_meta.get("organization_count_approx"),
            "is_default": True,
            "source": "workbook",
        },
        {
            "id": SECONDARY_BENCHMARK_ID,
            "label": high_meta.get("label", "High Engagement Benchmark"),
            "short_label": high_meta.get("short_label", "High Engagement"),
            "pct_column": "Benchmark2Pct",
            "gap_column": "GapVsBenchmark2",
            "description": high_meta.get("population_description", "High Engagement AI-Ready Leader benchmark comparison."),
            "methodology_note": high_meta.get("methodology_note", ""),
            "selection_rule": high_meta.get("selection_rule", ""),
            "footnote_context": high_meta.get("footnote_context", ""),
            "participant_count_approx": high_meta.get("participant_count_approx"),
            "organization_count_approx": high_meta.get("organization_count_approx"),
            "is_default": False,
            "source": "fixed_reference",
        },
    ]


# Kept as a compatibility constant for modules/tests that may import it.
BENCHMARK_COLUMN_SETS = benchmark_configs()


def _fixed_benchmark_for_row(row: pd.Series, values: dict) -> float:
    dtype = str(row.get("DataType", "")).strip().lower()
    if dtype == "overall":
        value = values.get("overall")
        if value is None:
            raise KeyError("overall")
        return float(value)
    if dtype == "composite":
        key = normalize_responsibility_name(row.get("CompositeName"))
        if key not in values.get("composites", {}):
            raise KeyError(f"composite:{key}")
        return float(values["composites"][key])
    if dtype == "construct":
        key = str(row.get("Construct", "")).strip()
        if key not in values.get("constructs", {}):
            raise KeyError(f"construct:{key}")
        return float(values["constructs"][key])
    raise KeyError(f"datatype:{dtype or '<blank>'}")


def apply_fixed_secondary_benchmark(data: pd.DataFrame, path: str | Path | None = None) -> pd.DataFrame:
    """Add the canonical High Engagement benchmark and gap to every report data row.

    The same AIRL benchmark value is used for Overall and every subgroup cut at the
    corresponding measurement grain. Any workbook-supplied secondary benchmark
    columns are overwritten so the bundled reference remains the single source of truth.
    """
    definitions = load_benchmark_definitions(path)
    values = (definitions.get("benchmarks", {}).get(SECONDARY_BENCHMARK_ID, {}) or {}).get("values", {})
    if not values:
        raise ValueError("High Engagement benchmark reference contains no values")

    out = data.copy()
    resolved = []
    missing = []
    for idx, row in out.iterrows():
        try:
            resolved.append(_fixed_benchmark_for_row(row, values))
        except KeyError as exc:
            missing.append((idx, str(exc).strip("'")))
            resolved.append(float("nan"))
    if missing:
        samples = ", ".join(key for _, key in missing[:8])
        suffix = "" if len(missing) <= 8 else f" (+{len(missing)-8} more)"
        raise ValueError(
            "Fixed High Engagement benchmark is missing mappings for workbook rows: " + samples + suffix
        )

    out["Benchmark2Pct"] = pd.Series(resolved, index=out.index, dtype="float64")
    target = pd.to_numeric(out["TargetHitPct"], errors="coerce")
    if target.isna().any():
        bad = target[target.isna()].index.tolist()[:8]
        raise ValueError(f"TargetHitPct must be numeric to calculate High Engagement benchmark gaps; invalid rows: {bad}")
    out["GapVsBenchmark2"] = target - out["Benchmark2Pct"]
    return out


def available_benchmarks(columns=None) -> list[dict]:
    """Return benchmark definitions available to the report.

    Overall remains workbook-sourced. The High Engagement benchmark is bundled and
    deterministically derived during content-model construction, so it no longer
    depends on optional workbook columns.
    """
    benchmarks = [dict(cfg) for cfg in benchmark_configs()]
    for benchmark in benchmarks:
        benchmark["is_default"] = benchmark["id"] == DEFAULT_BENCHMARK_ID
    return benchmarks


def default_benchmark_id(model: dict) -> str:
    benchmarks = model.get("benchmarks") or [dict(benchmark_configs()[0])]
    for benchmark in benchmarks:
        if benchmark.get("is_default"):
            return benchmark.get("id", DEFAULT_BENCHMARK_ID)
    return benchmarks[0].get("id", DEFAULT_BENCHMARK_ID)


def benchmark_by_id(model: dict, benchmark_id: str | None = None) -> dict:
    benchmarks = model.get("benchmarks") or [dict(benchmark_configs()[0])]
    selected = benchmark_id or default_benchmark_id(model)
    for benchmark in benchmarks:
        if benchmark.get("id") == selected:
            return benchmark
    return benchmarks[0]


def benchmark_views(model: dict) -> dict:
    views = model.get("benchmark_views") or {}
    if views:
        return views
    default_id = default_benchmark_id(model)
    return {
        default_id: {
            "benchmark": benchmark_by_id(model, default_id),
            "metrics": model.get("metrics", {}),
            "heatmaps": model.get("heatmaps", {}),
        }
    }


def model_for_benchmark(model: dict, benchmark_id: str) -> dict:
    """Return a rendering view with metrics/heatmaps switched to benchmark_id."""
    views = benchmark_views(model)
    view = views.get(benchmark_id) or views.get(default_benchmark_id(model)) or next(iter(views.values()))
    out = deepcopy(model)
    out["active_benchmark_id"] = benchmark_id
    out["active_benchmark"] = view.get("benchmark") or benchmark_by_id(model, benchmark_id)
    out["metrics"] = deepcopy(view.get("metrics") or model.get("metrics", {}))
    out["heatmaps"] = deepcopy(view.get("heatmaps") or model.get("heatmaps", {}))
    return out


def narrative_for_benchmark(model: dict, benchmark_id: str) -> dict:
    """Return shared narrative overlaid with benchmark-specific narrative."""
    shared = dict(model.get("narrative") or {})
    benchmark_specific = (model.get("benchmark_narratives") or {}).get(benchmark_id) or {}
    shared.update(benchmark_specific)
    return shared
