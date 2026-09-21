"""Deterministic display-state helpers for AIRL report rendering.

This module owns view-model decisions that sit between the content model and
HTML assembly, especially subgroup heatmap display states. It should not contain
LLM narrative generation or client data calculations.
"""
from __future__ import annotations

from airl_render_helpers import esc


def pick_high_low(rows):
    """Return the lowest-gap and highest-gap rows from a heatmap-like row list."""
    if not rows:
        return None, None
    rows_sorted = sorted(rows, key=lambda x: float(x.get("overall_gap", 0)))
    return rows_sorted[0], rows_sorted[-1]


def benchmark_title(client, avg_gap):
    """Return the deterministic Benchmark Comparison heading for the score pattern."""
    if avg_gap >= 2:
        return f"{client} outperforms the AI-Ready Leader benchmark across the full leadership operating system."
    if avg_gap >= 0:
        return f"{client} is broadly in line with the AI-Ready Leader benchmark, with targeted opportunities to strengthen consistency."
    return f"{client} trails the AI-Ready Leader benchmark overall, creating a focused case for targeted leadership enablement."


SUBGROUP_LIMITED_COPY = {
    "function": {
        "limited_headline": "Function-level patterns can reveal where AI leadership signals may concentrate.",
        "missing_text": "Function data are not available for benchmark comparison in this workbook. Additional assessment coverage would make it possible to identify where AI leadership signals may be stronger, weaker, or require different enablement across the organization.",
        "one_label": "function",
        "one_text_template": "The heatmap shows <b>{subgroup}</b> because it is the only function with comparison data available in this workbook. Additional assessment coverage would be needed before making broader subgroup comparisons.",
    },
    "level": {
        "limited_headline": "Leadership-layer patterns can reveal where AI leadership signals may need different support.",
        "missing_text": "Job level data are not available for benchmark comparison in this workbook. Additional assessment coverage would make it possible to compare where leadership signals may differ by layer.",
        "one_label": "level",
        "one_text_template": "The heatmap shows <b>{subgroup}</b> because it is the only job level with comparison data available in this workbook. Additional assessment coverage would be needed before making broader subgroup comparisons.",
    },
    "region": {
        "limited_headline": "Regional patterns can reveal where AI leadership signals may need local context.",
        "missing_text": "Region data are not available for benchmark comparison in this workbook. Additional assessment coverage would make it possible to compare how AI leadership signals may vary across geographies.",
        "one_label": "region",
        "one_text_template": "The heatmap shows <b>{subgroup}</b> because it is the only region with comparison data available in this workbook. Additional assessment coverage would be needed before making broader subgroup comparisons.",
    },
}


def coverage_note(section_type, model):
    """Return deterministic copy for unavailable subgroup heatmap comparisons."""
    cfg = SUBGROUP_LIMITED_COPY.get(section_type)
    if cfg:
        return cfg["missing_text"]
    return "Subgroup data are not available for benchmark comparison in this workbook. Additional assessment coverage would be needed before making broader subgroup comparisons."


def single_row_note(section_type, model, row):
    """Return deterministic copy when exactly one subgroup has heatmap data."""
    cfg = SUBGROUP_LIMITED_COPY.get(section_type, SUBGROUP_LIMITED_COPY["function"])
    subgroup = esc(row.get("cut_name", f"the available {cfg['one_label']}"))
    return cfg["one_text_template"].format(subgroup=subgroup)


def coverage_box(section_type, model, row=None):
    text = single_row_note(section_type, model, row) if row else coverage_note(section_type, model)
    return f'<div class="coverage-note"><span class="coverage-note-body">{text}</span></div>'


def limited_heatmap_headline(section_type):
    cfg = SUBGROUP_LIMITED_COPY.get(section_type)
    return cfg["limited_headline"] if cfg else "Additional subgroup coverage would add useful comparison context."


def heatmap_section_classes(section_type, state):
    """Return the CSS class string for a subgroup heatmap display state."""
    heat_classes = ["panel", "heat"]
    if section_type == "function":
        heat_classes.append("functional-heat")
    if state == "empty":
        heat_classes.extend(["heat-limited", f"{section_type}-heat-limited"])
    elif state == "single_row":
        heat_classes.extend(["heat-limited", "heat-single-row", f"{section_type}-heat-limited"])
    return " ".join(heat_classes)


def heatmap_section_state(section_type, model):
    """Return deterministic display state for a subgroup heatmap section."""
    rows = model.get("heatmaps", {}).get(section_type, [])
    if not rows:
        return {"state": "empty", "rows": rows, "classes": heatmap_section_classes(section_type, "empty")}
    if len(rows) == 1:
        return {"state": "single_row", "rows": rows, "classes": heatmap_section_classes(section_type, "single_row")}
    return {"state": "full", "rows": rows, "classes": heatmap_section_classes(section_type, "full")}


def heat_takeaways(prefix, n, client):
    return f'''<div class="heat-takeaways"><div class="heat-takeaway"><b>{n[prefix + '_meaning_1_title']}</b><span>{n[prefix + '_meaning_1_text']}</span></div><div class="heat-takeaway"><b>{n[prefix + '_meaning_2_title']}</b><span>{n[prefix + '_meaning_2_text']}</span></div><div class="heat-takeaway"><b>{n[prefix + '_meaning_3_title']}</b><span>{n[prefix + '_meaning_3_text']}</span></div></div>'''


def render_heatmap_section(section_id, kicker, title, section_type, model, n, client, table_html, guide_text):
    """Render a subgroup heatmap section from deterministic display state."""
    section_state = heatmap_section_state(section_type, model)
    rows = section_state["rows"]
    classes = section_state["classes"]
    if section_state["state"] == "empty":
        limited_title = limited_heatmap_headline(section_type)
        return f'<section id="{section_id}" class="{classes}"><div class="section-kicker">{kicker}</div><h2>{limited_title}</h2>{coverage_box(section_type, model)}</section>'
    if section_state["state"] == "single_row":
        limited_title = limited_heatmap_headline(section_type)
        return f'<section id="{section_id}" class="{classes}"><div class="section-kicker">{kicker}</div><h2>{limited_title}</h2><div class="heat-scroll">{table_html}</div>{coverage_box(section_type, model, rows[0])}</section>'
    return f'<section id="{section_id}" class="{classes}"><div class="section-kicker">{kicker}</div><h2>{title}</h2><div class="heat-scroll">{table_html}</div>{heat_takeaways(section_type, n, client)}<p class="heat-interpretation-footnote"><b>Interpretation Guide:</b> {guide_text}</p></section>'
