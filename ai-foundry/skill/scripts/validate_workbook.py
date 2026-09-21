#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
import pandas as pd

REQUIRED = {
    "demographics": [
        "CIQUltimateParentName", "AssmtKey", "CompletedYear", "CompletedDate",
        "Region", "FunctionName", "LevelName", "AssessmentType"
    ],
    "data": [
        "CutType", "CutName", "DataType", "KF4D_Code", "Construct", "CompositeName",
        "ParticipantCount", "TargetHitPct", "BenchmarkPct", "GapVsBenchmark"
    ],
}

from airl_constants import (
    AI_READY_RESPONSIBILITY_ORDER as REQUIRED_RESPONSIBILITIES,
    normalize_responsibility_name,
)

NUMERIC_COLUMNS = ["ParticipantCount", "TargetHitPct", "BenchmarkPct", "GapVsBenchmark"]
OPTIONAL_BENCHMARK_COLUMNS = ["Benchmark2Pct", "GapVsBenchmark2"]


def norm_text(value):
    return str(value).strip() if pd.notna(value) else ""


def validate(path: Path) -> int:
    if not path.exists():
        print(f"ERROR: workbook not found: {path}")
        return 2
    xls = pd.ExcelFile(path)
    ok = True
    for sheet, cols in REQUIRED.items():
        if sheet not in xls.sheet_names:
            print(f"ERROR: missing required sheet: {sheet}")
            ok = False
            continue
        df = pd.read_excel(path, sheet_name=sheet, nrows=5)
        missing = [c for c in cols if c not in df.columns]
        if missing:
            print(f"ERROR: sheet '{sheet}' missing columns: {missing}")
            ok = False
        else:
            print(f"OK: sheet '{sheet}' contains required columns")
    if not ok:
        return 1

    demo = pd.read_excel(path, sheet_name="demographics")
    data = pd.read_excel(path, sheet_name="data")

    # Required client identity should be present and unambiguous enough to render.
    legal_names = demo["CIQUltimateParentName"].dropna().astype(str).str.strip()
    legal_names = legal_names[legal_names.ne("")]
    if legal_names.empty:
        print("ERROR: demographics.CIQUltimateParentName has no nonblank client legal name")
        ok = False
    else:
        print(f"OK: found client legal name: {legal_names.iloc[0]}")
        if legal_names.nunique() > 1:
            print(f"WARNING: found {legal_names.nunique()} distinct CIQUltimateParentName values; the first nonblank value will be used")

    # The High Engagement benchmark is supplied by the skill reference, not the client workbook.
    # Legacy Benchmark2Pct / GapVsBenchmark2 columns are accepted for transition but are
    # informational only; build_content_model.py overwrites them from the canonical reference.
    present_optional = [col for col in OPTIONAL_BENCHMARK_COLUMNS if col in data.columns]
    if present_optional:
        print("INFO: workbook contains legacy second-benchmark column(s); canonical High Engagement values will be recalculated by the skill")
    numeric_columns = list(NUMERIC_COLUMNS)

    # Numeric type and range checks.
    for col in numeric_columns:
        numeric = pd.to_numeric(data[col], errors="coerce")
        invalid = int(numeric.isna().sum())
        if invalid:
            print(f"ERROR: data.{col} has {invalid} nonnumeric or missing value(s)")
            ok = False
            continue
        if col == "ParticipantCount":
            bad = int((numeric < 0).sum())
            if bad:
                print(f"ERROR: data.{col} has {bad} negative value(s)")
                ok = False
        elif col in ("TargetHitPct", "BenchmarkPct", "Benchmark2Pct"):
            bad = int(((numeric < 0) | (numeric > 100)).sum())
            if bad:
                print(f"ERROR: data.{col} has {bad} value(s) outside 0-100")
                ok = False
        elif col in ("GapVsBenchmark", "GapVsBenchmark2"):
            bad = int(((numeric < -100) | (numeric > 100)).sum())
            if bad:
                print(f"ERROR: data.{col} has {bad} value(s) outside -100 to +100")
                ok = False
    if ok:
        print("OK: required numeric columns are numeric and within expected bounds")

    # Duplicate aggregate-row detection. A duplicate here can double-count or
    # silently average a row that should be unique in the report model.
    key_cols = ["CutType", "CutName", "DataType", "KF4D_Code", "Construct", "CompositeName"]
    dup_mask = data[key_cols].fillna("").astype(str).apply(lambda col: col.str.strip()).duplicated(keep=False)
    dup_count = int(dup_mask.sum())
    if dup_count:
        print(f"ERROR: data sheet contains {dup_count} row(s) with duplicate aggregate keys {key_cols}")
        ok = False
    else:
        print("OK: no duplicate aggregate rows found")

    # Required responsibility coverage for Overall composite rows.
    data_work = data.copy()
    for col in ["DataType", "CutType", "CutName", "CompositeName"]:
        data_work[col] = data_work[col].map(norm_text)
    data_work["CompositeNameNorm"] = data_work["CompositeName"].map(normalize_responsibility_name)
    overall_comp = data_work[
        data_work["DataType"].str.casefold().eq("composite")
        & data_work["CutType"].str.casefold().eq("overall")
    ]
    found = set(overall_comp["CompositeNameNorm"])
    missing_resp = [r for r in REQUIRED_RESPONSIBILITIES if r not in found]
    if missing_resp:
        print(f"ERROR: missing required Overall/Composite responsibility row(s): {missing_resp}")
        ok = False
    else:
        print("OK: found all six required Overall/Composite responsibility rows")

    # Light gap consistency check with tolerance for SQL/rounding differences.
    target = pd.to_numeric(data["TargetHitPct"], errors="coerce")
    benchmark = pd.to_numeric(data["BenchmarkPct"], errors="coerce")
    gap = pd.to_numeric(data["GapVsBenchmark"], errors="coerce")
    delta = (target - benchmark - gap).abs()
    mismatch = int((delta > 1.0).sum())
    if mismatch:
        print(f"WARNING: {mismatch} row(s) have GapVsBenchmark more than 1.0 point away from TargetHitPct - BenchmarkPct")
    else:
        print("OK: GapVsBenchmark is directionally consistent with TargetHitPct - BenchmarkPct")

    if "ClientName" in data.columns or "ClientName" in demo.columns:
        source = "data" if "ClientName" in data.columns else "demographics"
        values = data["ClientName"] if source == "data" else demo["ClientName"]
        names = values.dropna().astype(str).str.strip()
        names = sorted({name for name in names if name}, key=lambda value: value.casefold())
        print(f"OK: found optional ClientName column on {source} sheet with {len(names)} distinct nonblank client record value(s)")
    else:
        print("INFO: no optional ClientName column found; client record footnote will be omitted")

    data_types = set(data["DataType"].astype(str).str.strip().str.lower())
    for val in ["Composite", "Construct"]:
        if val.lower() not in data_types:
            print(f"WARNING: no DataType={val} rows found")
    if "overall" in data_types:
        overall_rows = data[
            data["DataType"].astype(str).str.strip().str.lower().eq("overall")
            & data["CutType"].astype(str).str.strip().str.lower().eq("overall")
        ]
        if len(overall_rows) == 1:
            print("OK: found DataType=Overall row for Benchmark Comparison overall bar")
        elif len(overall_rows) > 1:
            print(f"WARNING: found {len(overall_rows)} DataType=Overall rows; the first Overall/Overall row will be used")
        else:
            print("WARNING: DataType=Overall is present, but no CutType=Overall row was found")
    else:
        print("INFO: no DataType=Overall row found; Benchmark Comparison overall bar will use the composite-average fallback")
    for val in ["Overall", "Function", "Level", "Region"]:
        if val.lower() not in set(data["CutType"].astype(str).str.strip().str.lower()):
            print(f"WARNING: no CutType={val} rows found")
    print("Validation complete")
    return 0 if ok else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: validate_workbook.py <workbook.xlsx>")
        sys.exit(2)
    sys.exit(validate(Path(sys.argv[1])))
