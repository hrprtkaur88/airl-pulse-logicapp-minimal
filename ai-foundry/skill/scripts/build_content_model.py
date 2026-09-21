#!/usr/bin/env python3
import argparse, json, re
from pathlib import Path
import pandas as pd
import numpy as np

from airl_constants import (
    AI_READY_RESPONSIBILITY_DEFINITIONS as DEFINITIONS,
    AI_READY_RESPONSIBILITY_DISPLAY as DISPLAY,
    AI_READY_RESPONSIBILITY_ORDER as ORDER,
    normalize_responsibility_name,
)
from airl_benchmarks import apply_fixed_secondary_benchmark, available_benchmarks

def clean_series(s):
    return s.dropna().astype(str).str.strip().replace({"nan": np.nan, "None": np.nan, "": np.nan}).dropna()

def common_name(legal):
    name = str(legal).strip()
    name = re.sub(r",?\s+(Inc\.?|LLC|Ltd\.?|Limited|S\.A\.|PLC|plc|Corporation|Corp\.?)$", "", name).strip()
    name = name.replace("Group Public Limited Company", "").strip()
    return name or str(legal).strip()

LEVEL_ORDER = [
    "Executive",
    "Senior Leader",
    "Mid Level Manager",
    "Front Line Manager",
    "Individual Contributor",
]

def records(series, labels=None):
    counts = series.value_counts()
    if labels is not None:
        ordered = [label for label in labels if label in counts.index]
        ordered.extend([label for label in counts.index if label not in ordered])
        counts = counts.reindex(ordered)
    total = int(counts.sum())
    return [{"label": str(k), "count": int(v), "pct": (float(v) / total * 100 if total else 0)} for k, v in counts.items()]

def client_records(*frames):
    """Return alphabetized distinct client record names from optional ClientName columns.

    Prefer the first sheet that contains usable ClientName values so that future
    data-tab exports are authoritative, while still accepting workbook versions
    that carry the same column on demographics. Values are displayed exactly as
    supplied after trimming whitespace.
    """
    for frame in frames:
        if frame is None or "ClientName" not in frame.columns:
            continue
        values = clean_series(frame["ClientName"]).tolist()
        if not values:
            continue
        distinct = sorted(set(values), key=lambda value: value.casefold())
        return distinct
    return []

def year_records(series):
    cleaned = clean_series(series)
    years = pd.to_numeric(cleaned, errors="coerce").dropna().astype(int)
    counts = years.value_counts().sort_index()
    total = int(counts.sum())
    return [{"label": str(k), "count": int(v), "pct": (float(v) / total * 100 if total else 0)} for k, v in counts.items()]

def pivot(comp, cut_type, value):
    d = comp[comp["CutType"].eq(cut_type)].copy()
    if d.empty or value not in d.columns:
        return pd.DataFrame(columns=ORDER)
    p = d.pivot_table(index="CutName", columns="CompositeName", values=value, aggfunc="mean")
    cols = [c for c in ORDER if c in p.columns]
    return p[cols]

def heatmap(comp, cut_type, gap_col="GapVsBenchmark"):
    gaps = pivot(comp, cut_type, gap_col)
    scores = pivot(comp, cut_type, "TargetHitPct")
    if gaps.empty:
        return []
    avg = gaps.mean(axis=1).sort_values(ascending=True)
    rows = []
    for cut in avg.index:
        n_vals = comp[(comp["CutType"].eq(cut_type)) & (comp["CutName"].eq(cut))]["ParticipantCount"]
        cells = []
        for c in ORDER:
            if c in gaps.columns:
                cells.append({
                    "responsibility": c,
                    "display": DISPLAY[c],
                    "score": float(scores.loc[cut, c]),
                    "gap": float(gaps.loc[cut, c]),
                })
        rows.append({
            "cut_name": str(cut),
            "n": int(n_vals.max()) if len(n_vals) else None,
            "overall_gap": float(avg.loc[cut]),
            "overall_score": float(np.nanmean([cell["score"] for cell in cells])) if cells else None,
            "cells": cells,
        })
    return rows


def subgroup_coverage(demo, heatmaps):
    """Describe which subgroup comparison sections have usable score rows.

    Coverage notes are workbook-driven. Web context should not be used to infer
    whether a client should have function, level, or region comparisons; the
    rendered report should only state what the uploaded workbook supports.
    """
    fields = {
        "function": "FunctionName",
        "level": "LevelName",
        "region": "Region",
    }
    coverage = {}
    for key, column in fields.items():
        dist = records(clean_series(demo[column]), LEVEL_ORDER if key == "level" else None) if column in demo.columns else []
        coverage[key] = {
            "has_score_rows": bool(heatmaps.get(key)),
            "demographic_group_count": len(dist),
            "demographic_groups": dist,
        }
    return coverage

def first_valid_number(row, column):
    value = row.get(column)
    if pd.isna(value):
        return None
    return float(value)

def overall_benchmark_metrics(data, composite_overall, benchmark):
    """Return overall score/benchmark/gap for the active benchmark view.

    New workbook exports include a single DataType=Overall row. That row is
    the authoritative source for the [Client] Overall bar. Older workbooks do
    not have this row, so preserve the historical composite-average fallback.
    """
    bench_col = benchmark["pct_column"]
    gap_col = benchmark["gap_column"]
    overall_rows = data[
        data["DataType"].str.lower().eq("overall")
        & data["CutType"].str.lower().eq("overall")
    ].copy()

    if not overall_rows.empty:
        preferred = overall_rows[overall_rows["CutName"].str.lower().eq("overall")]
        row = preferred.iloc[0] if not preferred.empty else overall_rows.iloc[0]
        return {
            "overall_average_score": first_valid_number(row, "TargetHitPct"),
            "overall_average_benchmark": first_valid_number(row, bench_col),
            "average_gap_vs_benchmark": first_valid_number(row, gap_col),
            "overall_source": "datatype_overall",
        }

    return {
        "overall_average_score": float(composite_overall["TargetHitPct"].mean()),
        "overall_average_benchmark": float(composite_overall[bench_col].mean()),
        "average_gap_vs_benchmark": float(composite_overall[gap_col].mean()),
        "overall_source": "composite_average_fallback",
    }



def advantage_label(record):
    """Return the client-facing label for the highest responsibility gap."""
    return "Largest Advantage" if float(record.get("gap_vs_benchmark", 0)) > 0 else "Relative Strength"


def watch_area_context(record):
    """Return context metadata for the lowest responsibility gap."""
    gap = float(record.get("gap_vs_benchmark", 0))
    if gap > 0:
        return "lowest_positive"
    if gap == 0:
        return "at_benchmark"
    return "below_benchmark"


def overall_records_for_benchmark(overall, benchmark):
    bench_col = benchmark["pct_column"]
    gap_col = benchmark["gap_column"]
    records_out = []
    for _, r in overall.iterrows():
        records_out.append({
            "responsibility": r["CompositeName"],
            "display": DISPLAY.get(r["CompositeName"], r["CompositeName"]),
            "definition": DEFINITIONS.get(r["CompositeName"], ""),
            "participant_count": int(r["ParticipantCount"]),
            "target_hit_pct": float(r["TargetHitPct"]),
            "benchmark_pct": float(r[bench_col]),
            "gap_vs_benchmark": float(r[gap_col]),
        })
    return records_out


def construct_records_for_benchmark(cons, benchmark, ascending=False):
    if cons.empty:
        return []
    gap_col = benchmark["gap_column"]
    bench_col = benchmark["pct_column"]
    oc = cons[cons["CutType"].eq("Overall")].copy()
    rows = []
    for _, r in oc.sort_values(gap_col, ascending=ascending).head(5).iterrows():
        rows.append({
            "Construct": str(r.get("Construct", "")),
            "CompositeName": str(r.get("CompositeName", "")),
            "TargetHitPct": float(r.get("TargetHitPct", 0)),
            "BenchmarkPct": float(r.get(bench_col, 0)),
            "GapVsBenchmark": float(r.get(gap_col, 0)),
        })
    return rows


def metrics_for_benchmark(data, overall, cons, benchmark):
    records_out = overall_records_for_benchmark(overall, benchmark)
    overall_metrics = overall_benchmark_metrics(data, overall, benchmark)
    largest = max(records_out, key=lambda x: x["gap_vs_benchmark"])
    watch = min(records_out, key=lambda x: x["gap_vs_benchmark"])
    return {
        "overall_average_score": overall_metrics["overall_average_score"],
        "overall_average_benchmark": overall_metrics["overall_average_benchmark"],
        "average_gap_vs_benchmark": overall_metrics["average_gap_vs_benchmark"],
        "overall_source": overall_metrics["overall_source"],
        "responsibilities": records_out,
        "largest_advantage": largest,
        "largest_advantage_label": advantage_label(largest),
        "watch_area": watch,
        "watch_area_context": watch_area_context(watch),
        "top_constructs": construct_records_for_benchmark(cons, benchmark, ascending=False),
        "watchpoint_constructs": construct_records_for_benchmark(cons, benchmark, ascending=True),
    }


def heatmaps_for_benchmark(comp, benchmark):
    gap_col = benchmark["gap_column"]
    return {
        "function": heatmap(comp, "Function", gap_col),
        "level": heatmap(comp, "Level", gap_col),
        "region": heatmap(comp, "Region", gap_col),
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workbook")
    ap.add_argument("--definitions", default=None)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    path = Path(args.workbook)
    demo = pd.read_excel(path, sheet_name="demographics")
    data = pd.read_excel(path, sheet_name="data")

    for col in ["DataType", "CompositeName", "CutType", "CutName"]:
        data[col] = data[col].astype(str).str.strip()
    data["CompositeName"] = data["CompositeName"].map(normalize_responsibility_name)
    demo["CompletedDate"] = pd.to_datetime(demo["CompletedDate"], errors="coerce")

    legal = clean_series(demo["CIQUltimateParentName"]).iloc[0]
    short = common_name(legal)
    comp = data[data["DataType"].str.lower().eq("composite")].copy()
    cons = data[data["DataType"].str.lower().eq("construct")].copy()

    overall = comp[comp["CutType"].eq("Overall")].copy()
    present = set(overall["CompositeName"].dropna().astype(str))
    missing = [name for name in ORDER if name not in present]
    if missing:
        missing_display = ", ".join(DISPLAY.get(name, name) for name in missing)
        raise ValueError(
            "Overall composite rows are missing required AI-Ready Leader responsibilities after alias normalization: "
            + missing_display
        )
    overall = overall.set_index("CompositeName").reindex(ORDER).reset_index()

    # Apply the canonical fixed High Engagement benchmark only after core workbook
    # responsibility coverage has been validated so missing AIRL rows fail clearly.
    data = apply_fixed_secondary_benchmark(data)
    comp = data[data["DataType"].str.lower().eq("composite")].copy()
    cons = data[data["DataType"].str.lower().eq("construct")].copy()
    overall = comp[comp["CutType"].eq("Overall")].copy().set_index("CompositeName").reindex(ORDER).reset_index()
    benchmarks = available_benchmarks(data.columns)
    benchmark_views = {}
    for benchmark in benchmarks:
        bid = benchmark["id"]
        benchmark_views[bid] = {
            "benchmark": benchmark,
            "metrics": metrics_for_benchmark(data, overall, cons, benchmark),
            "heatmaps": heatmaps_for_benchmark(comp, benchmark),
        }
    default_benchmark = next((b for b in benchmarks if b.get("is_default")), benchmarks[0])
    default_view = benchmark_views[default_benchmark["id"]]

    definitions = []
    if args.definitions and Path(args.definitions).exists():
        try:
            defs = pd.read_excel(args.definitions)
            definitions = defs.fillna("").to_dict(orient="records")
        except Exception as e:
            definitions = [{"load_error": str(e)}]

    heatmaps = default_view["heatmaps"]

    model = {
        "client": {"legal_name": str(legal), "short_name": short},
        "demographics": {
            "total_participants": int(len(demo)),
            "earliest_assessment": demo["CompletedDate"].min().strftime("%Y-%m-%d") if demo["CompletedDate"].notna().any() else None,
            "latest_assessment": demo["CompletedDate"].max().strftime("%Y-%m-%d") if demo["CompletedDate"].notna().any() else None,
            "year_counts": year_records(demo["CompletedYear"]),
            "level_distribution": records(clean_series(demo["LevelName"]), LEVEL_ORDER),
            "region_distribution": records(clean_series(demo["Region"])),
            "assessment_type_distribution": records(clean_series(demo["AssessmentType"]).map(lambda x: str(x).replace("_", " ").title())),
        },
        "data_context": {
            "client_records": client_records(data, demo),
        },
        "benchmarks": benchmarks,
        "active_benchmark_id": default_benchmark["id"],
        "benchmark_views": benchmark_views,
        "benchmark_narratives": {benchmark["id"]: {} for benchmark in benchmarks},
        "metrics": default_view["metrics"],
        "heatmaps": heatmaps,
        "subgroup_coverage": subgroup_coverage(demo, heatmaps),
        "definitions": definitions,
        "external_context": {
            "employee_count": None,
            "ai_strategy_summary": "",
            "sources": [],
            "vetted_context_bullets": [],
        },
        "narrative_status": "draft",
        "narrative": {},
    }
    Path(args.out).write_text(json.dumps(model, indent=2), encoding="utf-8")
    print(args.out)

if __name__ == "__main__":
    main()
