#!/usr/bin/env python3
"""Report-section helpers for deterministic AIRL HTML rendering.

Keep these helpers free of narrative judgment. They normalize external-source
metadata, build deterministic About-the-Data notes, and resolve embedded assets.
"""
import math
from pathlib import Path
from airl_render_helpers import esc
from airl_external_sources import external_evidence_sources, is_url_backed, normalize_external_source, source_label_from_url

def format_employee_count(x):
    """Return an approximate rounded employee count for client-facing copy."""
    if x is None or x == "":
        return ""
    try:
        n = float(str(x).replace(",", ""))
    except Exception:
        return str(x)
    if n <= 0:
        return ""
    if n < 1000:
        base = 50 if n < 500 else 100
    elif n < 10000:
        base = 500 if n < 5000 else 1000
    elif n < 100000:
        base = 1000
    else:
        base = 5000 if n < 250000 else 10000
    rounded = int(math.floor(n / base) * base)
    if rounded <= 0:
        rounded = int(base)
    return f"{rounded:,}"

def data_interpretation_note(model, employee_text):
    """Render the About the Data interpretation note as concise bullets."""
    client = model["client"]["short_name"]
    demo = model["demographics"]
    client_records = model.get("data_context", {}).get("client_records", []) or []
    bullets = [
        f"This report reflects <b>{demo['total_participants']:,} assessed {esc(client)} participants</b>{employee_text}.",
        "Existing Korn Ferry Leadership Assessment data has been realigned to the <b>AI-Ready Leader Success Profile</b> to highlight directional leadership signals for leading in the age of AI.",
        "Results are based on the percentage of Korn Ferry competencies, traits, and drivers meeting or exceeding the Success Profile target, compared with the selected <b>Overall or High Engagement benchmark</b>.",
    ]
    if client_records:
        records = ", ".join(esc(name) for name in client_records)
        bullets.append(f"Data is included from the following Korn Ferry client records: <b>{records}</b>.")
    bullets.extend([
        "These findings should be interpreted as <b>indicative, not definitive</b>. The sample is not the full organization, assessment timing varies, and representation may differ by level, region, and function.",
        "Larger participant counts increase confidence in the patterns shown. Korn Ferry recommends at least <b>100 participants</b> for interpretation.",
    ])
    items = "".join(f"<li>{text}</li>" for text in bullets)
    return f'<div class="header-footnote"><b>Data interpretation note:</b><ul>{items}</ul></div>'



def external_sources_section(model):
    """Render a compact source list for non-workbook web context.

    External context sources must include URLs. Source titles are linked to
    URLs and paired with a concise inline purpose note; raw URLs are not
    printed as visible text in the report.
    """
    external_context = model.get("external_context", {}) or {}
    normalized = []
    seen = set()
    # Render display sources plus optional vetted evidence-ledger bullet sources.
    # The bullet claims themselves are not printed here; this remains a compact source list.
    for src in external_evidence_sources(external_context, infer_title=True):
        title = src.get("title", "").strip()
        url = src.get("url", "").strip()
        if not url or not is_url_backed(url):
            continue
        if not title:
            title = source_label_from_url(url)
        key = url.casefold()
        if key in seen:
            continue
        seen.add(key)
        src["title"] = title
        normalized.append(src)
    if not normalized:
        return ""
    links = []
    for src in normalized:
        title = esc(src.get("title") or source_label_from_url(src.get("url", "")))
        url = src.get("url", "").strip()
        purpose = src.get("purpose", "").strip()
        purpose_html = f' <span class="source-purpose">{esc(purpose)}</span>' if purpose else ""
        links.append(
            f'<li><a href="{esc(url)}" target="_blank" rel="noopener noreferrer">{title}</a>{purpose_html}</li>'
        )
    return '<section id="external-context-sources" class="external-sources"><div class="section-kicker">External context sources</div><p>Company headcount and AI/digital context were informed by:</p><ul>' + ''.join(links) + '</ul></section>'


EMBEDDED_KF_LOGO_DATA_URI = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAATYAAABZCAMAAACDt/igAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAKmUExURf///////////wAAAP///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////0CMfCB4ZmCfkv///////////////////zCCcQBlUP///////////////////////////////////////////////////////////////////////+/19K/PyM/i3v///////////5/Fvf///////////////////1CVh////////////////////3Cpnd/s6YCyqP///////////////////4+7shBvW////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////7/Y0////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////yObY5wAAADidFJOU+//rwAwYAwQUI+/z9+fQFRwKKilJoD+cgEpoiQg5VmpIcwqnR6zJ5ocDiuqlxmBlRb0aCyrkhTbTxHCNqyNHS2KkASthwl3////LoUG6l7//66C0UUv/X/XDft957cFV/h6PP///2/5bf9d6AOI4P91FaHHO////wKOX7oi//8bptJH86MzSHxM2Bd4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'


def load_kf_logo_src(skill_root):
    """Return the packaged Korn Ferry logo data URI with an embedded fallback."""
    logo_path = Path(skill_root) / "assets" / "korn_ferry_logo_data_uri.txt"
    logo_src = logo_path.read_text(encoding="utf-8").strip() if logo_path.exists() else EMBEDDED_KF_LOGO_DATA_URI
    if not logo_src:
        logo_src = EMBEDDED_KF_LOGO_DATA_URI
    return logo_src
