#!/usr/bin/env python3
"""Deterministic chart and heatmap HTML helpers for AIRL reports.

This module owns SVG/chart fragments, heatmap color decisions, and functional
Focus Area highlight-count logic. It intentionally does not assemble full report
sections or generate consulting narrative.
"""

from airl_constants import (
    AI_READY_RESPONSIBILITY_DISPLAY as DISPLAY,
    AI_READY_RESPONSIBILITY_ORDER as ORDER,
)
from airl_render_helpers import esc, gap, gap0, pct

COLORS = ["#05c690", "#00adbb", "#dad8d6", "#7aa99a", "#b8f4df", "#8fbcbc", "#9eddb8"]

HEATMAP_COLORS = {
    "strong_red": "#b94a42",
    "dark_red": "#c96f65",
    "medium_red": "#d88c83",
    "light_red": "#dfa39b",
    "very_light_red": "#edd0cc",
    "red_gray": "#e8d6d2",
    "neutral": "#dad8d6",
    "green_gray": "#d4ded8",
    "very_light_green": "#cfe9d8",
    "light_green": "#b7e1ca",
    "medium_green": "#91d6ad",
    "dark_green": "#72cb98",
    "strong_green": "#57c98c",
}


def pct_label(x):
    x = float(x)
    return "<1%" if 0 < x < 1 else f"{x:.0f}%"


def rounded_gap_value(v):
    """Return the integer gap value used for visible heatmap display and shading."""
    return round(float(v))


def heat_color(v):
    """Return heatmap cell color from the same rounded value shown in the cell.

    This keeps tiny differences from over-signaling directionality: values such
    as -0.4 round to 0, display as 0, and shade true neutral.
    """
    r = rounded_gap_value(v)
    if r <= -15: return HEATMAP_COLORS["strong_red"]
    if r <= -12: return HEATMAP_COLORS["dark_red"]
    if r <= -9: return HEATMAP_COLORS["medium_red"]
    if r <= -6: return HEATMAP_COLORS["light_red"]
    if r <= -3: return HEATMAP_COLORS["very_light_red"]
    if r <= -1: return HEATMAP_COLORS["red_gray"]
    if r == 0: return HEATMAP_COLORS["neutral"]
    if r <= 2: return HEATMAP_COLORS["green_gray"]
    if r <= 5: return HEATMAP_COLORS["very_light_green"]
    if r <= 8: return HEATMAP_COLORS["light_green"]
    if r <= 11: return HEATMAP_COLORS["medium_green"]
    if r <= 14: return HEATMAP_COLORS["dark_green"]
    return HEATMAP_COLORS["strong_green"]


def conic(records):
    acc = 0.0
    segs, legend, tips = [], [], []
    for i, r in enumerate(records):
        color = COLORS[i % len(COLORS)]
        p = float(r.get("pct", 0))
        segs.append(f"{color} {acc:.2f}% {acc+p:.2f}%")
        legend.append(f'<span><i style="background:{color}"></i>{esc(r["label"])} <b>{pct_label(p)}</b></span>')
        tips.append(f'{r["label"]}: {int(r["count"]):,}')
        acc += p
    return "conic-gradient(" + ", ".join(segs) + ")", "".join(legend), " | ".join(tips)


def bars(records):
    if not records:
        return ""
    mx = max(r["count"] for r in records) or 1
    return "".join(f'<div><span>{esc(r["label"])}</span><i style="width:{r["count"]/mx*100:.0f}%"></i><b>{int(r["count"]):,}</b></div>' for r in records)


def wrap(text, max_chars=58):
    words = str(text).split()
    out, line = [], ""
    for w in words:
        if len((line + " " + w).strip()) <= max_chars:
            line = (line + " " + w).strip()
        else:
            if line:
                out.append(line)
            line = w
    if line:
        out.append(line)
    return out[:2]


def function_focus_count(rows):
    """Return number of functional heatmap rows to highlight as Focus area.

    Highlights the lowest-opportunity cluster rather than a fixed count.
    Baseline: 0 for 1 group, 1 for 2-3, 2 for 4-5, 3 for 6+.
    Then adjusts for clear cluster breaks, strong-above-benchmark patterns,
    ties that would create visual clutter, and large below-benchmark clusters.
    """
    if not rows:
        return 0
    gaps = [float(r.get("overall_gap", 0)) for r in rows]
    n = len(gaps)
    if n <= 1:
        return 0
    if n <= 3:
        base = 1
    elif n <= 5:
        base = 2
    else:
        base = 3

    below_cluster = 0
    for g in gaps:
        if g <= -5:
            below_cluster += 1
        else:
            break
    if n >= 6 and below_cluster > base:
        return max(base, min(below_cluster, 6, max(1, n // 2)))

    count = min(base, n)

    if count < n:
        boundary = round(gaps[count - 1])
        end = count
        while end < n and round(gaps[end]) == boundary:
            end += 1
        if end > count:
            start = count - 1
            while start > 0 and round(gaps[start - 1]) == boundary:
                start -= 1
            if end > count and n <= 10 and start >= 2:
                count = start
            elif end > 3 and n <= 8 and start > 0:
                count = start
            else:
                count = end

    if gaps[0] >= 10:
        cluster = 1
        for i in range(1, n):
            if gaps[i] - gaps[i-1] >= 8:
                break
            cluster += 1
        if cluster < count:
            count = cluster

    if gaps[0] < 10:
        for i in range(1, min(count, n)):
            if gaps[i] - gaps[i-1] >= 5:
                count = i
                break

    return max(1, min(count, max(1, n // 2)))


def focus_row_indexes(rows, mark_count=0):
    """Return the row indexes that Python has decided should be visually marked.

    The template and browser script should only render and position the marker.
    They should not decide which functional rows are Focus Areas.
    """
    if mark_count == "function":
        mark_count = function_focus_count(rows)
    if not isinstance(mark_count, int) or mark_count <= 0 or not rows:
        return set()

    bounded_count = min(mark_count, len(rows))
    threshold = round(float(rows[bounded_count - 1]["overall_gap"]))
    indexes = {
        idx
        for idx, row in enumerate(rows)
        if round(float(row["overall_gap"])) <= threshold
    }
    if mark_count < len(indexes):
        indexes = set(range(bounded_count))
    return indexes


def focus_row_bounds(marked_indexes, total_rows):
    """Return first and last marked row index for CSS edge classes."""
    marked_order = [idx for idx in range(total_rows) if idx in marked_indexes]
    if not marked_order:
        return None, None
    return marked_order[0], marked_order[-1]


def function_focus_pill_style(mark_count):
    """Return initial CSS-variable style for the functional Focus Area pill.

    JavaScript may refine geometry after layout, but the decision to render the
    pill and its row span are owned by Python.
    """
    if mark_count <= 0:
        return ""
    header_h = 44
    row_h = 34
    block_h = max(row_h, mark_count * row_h)
    if mark_count == 1:
        height = 70
    elif mark_count == 2:
        height = 78
    else:
        height = min(112, max(88, block_h - 20))
    top = round(header_h + ((block_h - height) / 2))
    return f"--focus-pill-height:{height}px;--focus-pill-top:{top}px;"


def chart(model):
    client = model["client"]["short_name"]
    metrics = model["metrics"]
    resp = metrics["responsibilities"]
    rows = [{
        "display": f"{client} Overall",
        "definition": "Overall AI-Ready Leader result for the assessed population.",
        "target_hit_pct": metrics["overall_average_score"],
        "benchmark_pct": metrics["overall_average_benchmark"],
        "gap_vs_benchmark": metrics["average_gap_vs_benchmark"],
        "overall": True,
    }] + resp
    scale = 480 / 100
    parts = ['<svg viewBox="0 0 960 468" class="chart-svg" role="img" aria-label="AI Ready Leader benchmark comparison">']
    for i, r in enumerate(rows):
        y = 42 + i * 54
        if i == 1:
            parts.append('<line x1="0" y1="96" x2="960" y2="96" stroke="#d9e2de" stroke-width="1"/>')
            y += 8
        elif i > 1:
            y += 8
        label = r.get("display") or DISPLAY.get(r["responsibility"], r["responsibility"])
        definition = r.get("definition", "")
        parts.append(f'<text x="18" y="{y+18}" class="svg-label{" overall-label" if r.get("overall") else ""}">{esc(label)}</text>')
        tspans = "".join(f'<tspan x="18" dy="{14 if j == 0 else 13}">{esc(line)}</tspan>' for j, line in enumerate(wrap(definition)))
        parts.append(f'<text x="0" y="{y+18}" class="svg-def">{tspans}</text>')
        score = float(r["target_hit_pct"]); bench = float(r["benchmark_pct"]); g = float(r["gap_vs_benchmark"])
        tip = f"Client score: {score:.1f}% | Gap to benchmark: {g:+.1f}"
        bar_y = y + 12
        bar_cy = bar_y + 9
        parts.append(f'<rect x="350" y="{bar_y}" width="480" height="18" rx="9" fill="#e8eeeb"/>')
        parts.append(f'<rect x="350" y="{bar_y}" width="{score*scale:.1f}" height="18" rx="9" fill="#00634f" data-tooltip="{esc(tip)}"/>')
        parts.append(f'<circle cx="{350+bench*scale:.1f}" cy="{bar_cy}" r="8" fill="#05c690" data-tooltip="{esc(tip)}"/>')
        parts.append(f'<rect class="bar-hitarea" x="350" y="{bar_y-6}" width="540" height="34" fill="transparent" pointer-events="all" data-tooltip="{esc(tip)}"/>')
        parts.append(f'<text x="850" y="{bar_y+15}" class="svg-small strong">{pct(score)}</text>')
        parts.append(f'<text x="962" y="{bar_y+15}" class="svg-gap">{gap(g)}</text>')
    parts.append(f'<g class="chart-legend" transform="translate(350 452)"><circle cx="0" cy="0" r="7" fill="#05c690"/><text x="16" y="1" class="svg-key">Benchmark</text><rect x="122" y="-6" width="34" height="12" rx="6" fill="#00634f"/><text x="166" y="1" class="svg-key dark">{esc(client)} result</text></g>')
    parts.append('</svg>')
    return "".join(parts)


def heat_table(rows, mark_count=3):
    header = '<th>Population</th><th>Overall Gap</th>' + ''.join(f'<th>{esc(DISPLAY[c])}</th>' for c in ORDER)
    out = []
    marked_indexes = focus_row_indexes(rows, mark_count)
    first_mark, last_mark = focus_row_bounds(marked_indexes, len(rows))
    for idx, row in enumerate(rows):
        mark = idx in marked_indexes
        classes = []
        if mark:
            classes.append('priority-row')
            if idx == first_mark:
                classes.append('priority-first')
            if idx == last_mark:
                classes.append('priority-last')
        cls = f' class="{" ".join(classes)}"' if classes else ''
        tip = f'Client score: {row.get("overall_score", 0):.1f}% | Gap to benchmark: {row["overall_gap"]:+.1f}'
        cells = [f'<td class="overall-gap-cell" data-tooltip="{esc(tip)}" style="--heat:{heat_color(row["overall_gap"])}"><b>{gap0(row["overall_gap"])}</b></td>']
        by_resp = {c["responsibility"]: c for c in row["cells"]}
        for resp in ORDER:
            c = by_resp.get(resp)
            if c:
                tip = f'Client score: {c["score"]:.1f}% | Gap to benchmark: {c["gap"]:+.1f}'
                cells.append(f'<td data-tooltip="{esc(tip)}" style="--heat:{heat_color(c["gap"])}"><b>{gap0(c["gap"])}</b></td>')
            else:
                cells.append('<td></td>')
        n = f' <span class="inline-n">(n={row["n"]})</span>' if row.get("n") else ""
        out.append(f'<tr{cls}><td class="cut-name">{esc(row["cut_name"])}{n}</td>{"".join(cells)}</tr>')
    return f'<table class="heat-table"><thead><tr>{header}</tr></thead><tbody>{"".join(out)}</tbody></table>'


def function_heat_html(model):
    rows = model['heatmaps'].get('function', [])
    mark_count = function_focus_count(rows)
    label = ''
    if mark_count > 0:
        label = f'<div class="function-opportunity-label" style="{function_focus_pill_style(mark_count)}">Focus Area</div>'
    return label + heat_table(rows, mark_count)


def rank_list(rows):
    parts = []
    for r in rows:
        comp = DISPLAY.get(r.get("CompositeName"), r.get("CompositeName", ""))
        parts.append(f'<li><span>{esc(r.get("Construct", ""))}</span><b>{gap(r.get("GapVsBenchmark", 0))}</b><small>{esc(comp)} | {pct(r.get("TargetHitPct", 0))} target-hit</small></li>')
    return "".join(parts)
