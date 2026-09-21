"""Canonical slug rule for client_name used in every blob path. Define once."""
import re
import unicodedata

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def slugify(client_name: str) -> str:
    if not client_name or not client_name.strip():
        raise ValueError("client_name is required")
    normalized = unicodedata.normalize("NFD", client_name.strip().lower())
    stripped = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
    return _NON_ALNUM.sub("-", stripped).strip("-")


def data_csv_path(client_name: str, month_key_mmyyyy: str) -> str:
    return f"{slugify(client_name)}/export-file-{month_key_mmyyyy}.csv"


def data_workbook_path(client_name: str, month_key_mmyyyy: str) -> str:
    """Path for the AIRL assessment workbook (.xlsx) consumed by
    ai-foundry/skill/scripts/build_content_model.py. Supersedes
    data_csv_path() now that the pipeline generates AIRL-shaped workbooks
    instead of flat transactional CSVs."""
    return f"{slugify(client_name)}/assessment-workbook-{month_key_mmyyyy}.xlsx"


def report_dated_path(client_name: str, date_key_ddmmyyyy: str) -> str:
    return f"{slugify(client_name)}/report-file-{date_key_ddmmyyyy}.html"


def report_latest_path(client_name: str) -> str:
    return f"{slugify(client_name)}/report-file-latest.html"


def status_manifest_path(client_name: str, month_key_mmyyyy: str) -> str:
    return f"{slugify(client_name)}/status-{month_key_mmyyyy}.json"
