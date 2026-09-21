#!/usr/bin/env python3
"""Lightweight AIRL Pulse regression harness.

The harness uses synthetic content models and a small synthetic workbook to
protect high-risk behavior before renderer/template refactors. It is intended
for maintainers, not for client report generation.
"""
from __future__ import annotations

import copy
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from airl_constants import AI_READY_RESPONSIBILITY_ORDER as ORDER, AI_READY_RESPONSIBILITY_DISPLAY as DISPLAY
from airl_charts import function_focus_count, focus_row_indexes
from validate_content_model import validate_model, validate_model_issues, required_narrative_fields
from lint_narrative_labels import lint_benchmark_referential_framing


LONG = "This AI-ready leadership signal connects the workbook pattern to practical Human + AI execution choices for the client team."


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd or ROOT), text=True, capture_output=True)


def resp_record(name: str, gap: float, score_base: float = 70.0) -> dict:
    score = score_base + gap / 2
    bench = score - gap
    return {
        "responsibility": name,
        "display": DISPLAY.get(name, name),
        "definition": f"Synthetic definition for {DISPLAY.get(name, name)}.",
        "participant_count": 120,
        "target_hit_pct": score,
        "benchmark_pct": bench,
        "gap_vs_benchmark": gap,
    }


def heat_row(label: str, gap: float) -> dict:
    cells = []
    for idx, responsibility in enumerate(ORDER):
        rgap = gap + (idx - 2) * 0.4
        score = 70 + rgap / 2
        cells.append({
            "responsibility": responsibility,
            "display": DISPLAY.get(responsibility, responsibility),
            "score": score,
            "gap": rgap,
        })
    return {
        "cut_name": label,
        "n": 60,
        "overall_gap": gap,
        "overall_score": sum(c["score"] for c in cells) / len(cells),
        "cells": cells,
    }


def narrative(final: bool = True) -> dict:
    n = {
        "hero_h1": "AI-ready leadership strength can accelerate Human + AI execution.",
        "hero_p": "The client shows an AI-ready leadership pattern that can support focused transformation and practical scaling choices.",
        "executive_h2": "Readiness is strong enough to support AI activation where leaders are enabled with focus.",
        "executive_p1": "The overall pattern sits +4.0 points versus benchmark, suggesting AI-ready leadership capacity that can be converted into practical execution.",
        "executive_p2": "The strongest signals point to leaders who can mobilize change while the watch areas indicate where enablement should make AI adoption more consistent.",
        "commercial_implication": "Use this pattern to prioritize AI leader enablement, role-based deployment, and targeted follow-up conversations.",
        "largest_narrative": "This relative strength can help leaders sponsor Human + AI ways of working and translate ambition into execution momentum.",
        "watch_narrative": "This watch area should be reinforced so AI adoption is supported by clearer expectations and practical team routines.",
        "story_h2": "The data points to an AI-ready leadership base that needs targeted enablement to scale.",
        "story_card_1_title": "Activation capacity is present.",
        "story_card_1_text": LONG,
        "story_card_2_title": "Enablement must be targeted.",
        "story_card_2_text": LONG,
        "story_toggle_1_title": "Where leadership energy can scale AI.",
        "story_toggle_1_text": LONG,
        "story_toggle_2_title": "Where execution needs support.",
        "story_toggle_2_text": LONG,
        "story_toggle_3_title": "How to use subgroup variation.",
        "story_toggle_3_text": LONG,
        "story_toggle_4_title": "How to turn insight into action.",
        "story_toggle_4_text": LONG,
        "signals_high_text": "The highest differentiators indicate leadership behaviors that can support AI adoption and cross-functional scaling.",
        "signals_low_text": "The relative watchpoints indicate where AI enablement and reinforcement may need to be more deliberate.",
        "follow_up_opportunities": [
            {"title": "Prioritize AI-ready leader deployment", "text": "Use the strongest leadership signals to decide where AI adoption can be accelerated with sponsorship and visible role modeling."},
            {"title": "Build targeted enablement", "text": "Focus enablement on the watch areas so leaders can translate AI ambition into consistent team practices."},
            {"title": "Use subgroup patterns for sequencing", "text": "Sequence pilots and support based on the functions, levels, and regions that show the clearest readiness differences."},
            {"title": "Connect insights to transformation planning", "text": "Link assessment signals to broader Human + AI workforce planning, leadership development, and change activation."},
        ],
    }
    for section in ("function", "level", "region"):
        for idx in range(1, 4):
            n[f"{section}_meaning_{idx}_title"] = f"{section.title()} interpretation {idx}"
            n[f"{section}_meaning_{idx}_text"] = LONG
    return n


def base_model() -> dict:
    gaps = [7.0, 5.0, 4.0, 3.0, 1.0, -2.0]
    responsibilities = [resp_record(name, gap) for name, gap in zip(ORDER, gaps)]
    model = {
        "client": {"legal_name": "Example Enterprise plc", "short_name": "Example Enterprise"},
        "demographics": {
            "total_participants": 180,
            "earliest_assessment": "2025-01-02",
            "latest_assessment": "2025-12-12",
            "year_counts": [{"label": "2025", "count": 180, "pct": 100}],
            "level_distribution": [{"label": "Executive", "count": 90, "pct": 50}, {"label": "Senior Leader", "count": 90, "pct": 50}],
            "region_distribution": [{"label": "North America", "count": 90, "pct": 50}, {"label": "Europe", "count": 90, "pct": 50}],
            "assessment_type_distribution": [{"label": "Leadership", "count": 180, "pct": 100}],
        },
        "data_context": {"client_records": []},
        "metrics": {
            "overall_average_score": 72.0,
            "overall_average_benchmark": 68.0,
            "average_gap_vs_benchmark": 4.0,
            "overall_source": "datatype_overall",
            "responsibilities": responsibilities,
            "largest_advantage": responsibilities[0],
            "largest_advantage_label": "Largest Advantage",
            "watch_area": responsibilities[-1],
            "watch_area_context": "below_benchmark",
            "top_constructs": [
                {"Construct": f"Differentiator {i}", "CompositeName": ORDER[i % len(ORDER)], "TargetHitPct": 75 - i, "BenchmarkPct": 68 - i, "GapVsBenchmark": 7 - i}
                for i in range(5)
            ],
            "watchpoint_constructs": [
                {"Construct": f"Watchpoint {i}", "CompositeName": ORDER[i % len(ORDER)], "TargetHitPct": 62 - i, "BenchmarkPct": 64, "GapVsBenchmark": -2 - i}
                for i in range(5)
            ],
        },
        "heatmaps": {
            "function": [heat_row("Function A", -4.0), heat_row("Function B", 3.0), heat_row("Function C", 8.0)],
            "level": [heat_row("Executive", 5.0), heat_row("Senior Leader", -1.0)],
            "region": [heat_row("North America", 6.0), heat_row("Europe", -3.0)],
        },
        "subgroup_coverage": {},
        "definitions": [],
        "external_context": {
            "employee_count": "50,000",
            "ai_strategy_summary": "The client has public AI and digital transformation context that can inform framing.",
            "sources": [{"title": "Example source", "url": "https://example.com/ai", "purpose": "AI strategy context"}],
            "vetted_context_bullets": [],
        },
        "narrative_status": "final",
        "narrative": narrative(),
    }
    return model


def write_model(tmp: Path, name: str, model: dict) -> Path:
    path = tmp / f"{name}.json"
    path.write_text(json.dumps(model, indent=2), encoding="utf-8")
    return path


def strip_css_comments(css: str) -> str:
    """Remove CSS comments so tests only inspect active declarations."""
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def css_blocks(html: str, selector: str) -> list[str]:
    """Return active CSS declaration blocks for a selector, including comma-grouped selectors."""
    css = strip_css_comments(html)
    blocks: list[str] = []
    for match in re.finditer(r"([^{}]+)\{([^}]*)\}", css, re.S):
        selector_group = match.group(1)
        declarations = match.group(2)
        selectors = [part.strip() for part in selector_group.split(",")]
        if selector in selectors:
            blocks.append(declarations)
    return blocks


def assert_css_property(html: str, selector: str, prop: str, value: str) -> None:
    blocks = css_blocks(html, selector)
    if not blocks:
        raise AssertionError(f"missing CSS selector: {selector}")
    target = re.compile(rf"(?:^|;)\s*{re.escape(prop)}\s*:\s*{re.escape(value)}\s*(?:!important)?\s*(?:;|$)", re.I)
    if not any(target.search(block) for block in blocks):
        raise AssertionError(f"missing CSS property {prop}: {value} under selector {selector}")


def set_responsibility_gaps(model: dict, gaps: list[float]) -> dict:
    """Update the synthetic model to a coherent responsibility-gap pattern."""
    responsibilities = [resp_record(name, gap) for name, gap in zip(ORDER, gaps)]
    metrics = model["metrics"]
    metrics["responsibilities"] = responsibilities
    metrics["largest_advantage"] = max(responsibilities, key=lambda item: item["gap_vs_benchmark"])
    metrics["largest_advantage_label"] = "Largest Advantage" if metrics["largest_advantage"]["gap_vs_benchmark"] > 0 else "Relative Strength"
    metrics["watch_area"] = min(responsibilities, key=lambda item: item["gap_vs_benchmark"])
    metrics["watch_area_context"] = "below_benchmark" if metrics["watch_area"]["gap_vs_benchmark"] < 0 else "lowest_positive"
    avg_gap = sum(gaps) / len(gaps)
    metrics["average_gap_vs_benchmark"] = avg_gap
    metrics["overall_average_score"] = 70 + avg_gap / 2
    metrics["overall_average_benchmark"] = metrics["overall_average_score"] - avg_gap
    model["narrative"]["executive_p1"] = (
        f"The overall AI-ready leadership pattern sits {avg_gap:+.1f} points versus benchmark, "
        "creating a practical signal for Human + AI execution planning."
    )
    return model


def assert_no_issues(name: str, model: dict) -> None:
    issues = validate_model(model, strict=True)
    if issues:
        raise AssertionError(f"{name} unexpectedly failed validation: {issues}")


def assert_has_issue(name: str, model: dict, expected: str) -> None:
    issues = validate_model(model, strict=True)
    if not any(expected in issue for issue in issues):
        raise AssertionError(f"{name} did not produce expected issue containing {expected!r}. Issues: {issues}")


def test_full_model_renders(tmp: Path) -> None:
    model = base_model()
    assert_no_issues("full model", model)
    src = write_model(tmp, "full_model", model)
    out = tmp / "full_report.html"
    result = run([sys.executable, str(SCRIPTS / "render_report.py"), str(src), "--out", str(out)])
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    html = out.read_text(encoding="utf-8")
    required_fragments = [
        "id=\"about-data\"",
        "id=\"executive-narrative\"",
        "id=\"interpretive-storyline\"",
        "id=\"benchmark-comparison\"",
        "id=\"leadership-signals\"",
        "id=\"functional-patterns\"",
        "id=\"population-patterns\"",
        "id=\"regional-patterns\"",
        "id=\"follow-up-opportunities\"",
        "id=\"external-context-sources\"",
    ]
    for fragment in required_fragments:
        if fragment not in html:
            raise AssertionError(f"rendered HTML missing {fragment}")


def test_limited_heatmap_narrative_contract(tmp: Path) -> None:
    model = base_model()
    model["heatmaps"]["region"] = [heat_row("Only Region", 2.0)]
    for field in list(model["narrative"].keys()):
        if field.startswith("region_meaning_"):
            del model["narrative"][field]
    assert_no_issues("one-row heatmap", model)
    needed = required_narrative_fields(model)
    if any(field.startswith("region_meaning_") for field in needed):
        raise AssertionError("region meaning fields should not be required for one-row heatmap sections")

    model_two = copy.deepcopy(model)
    model_two["heatmaps"]["region"].append(heat_row("Second Region", -2.0))
    assert_has_issue("two-row heatmap", model_two, "region_meaning_1_title")


def test_narrative_escaping(tmp: Path) -> None:
    model = base_model()
    marker = "<script>alert('x')</script>"
    model["narrative"]["hero_h1"] = "AI readiness " + marker + " should render as escaped text for Human + AI safety."
    src = write_model(tmp, "escaping", model)
    out = tmp / "escaping.html"
    result = run([sys.executable, str(SCRIPTS / "render_report.py"), str(src), "--out", str(out)])
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    html = out.read_text(encoding="utf-8")
    if marker in html:
        raise AssertionError("raw script marker was not escaped")
    if "&lt;script&gt;alert" not in html:
        raise AssertionError("escaped script marker not found")


def test_final_validation_blocks_bad_narrative(tmp: Path) -> None:
    draft = base_model()
    draft["narrative_status"] = "draft"
    assert_has_issue("draft status", draft, "narrative_status")

    recs = base_model()
    recs["narrative"]["follow_up_opportunities"] = recs["narrative"]["follow_up_opportunities"][:3]
    assert_has_issue("three recommendations", recs, "exactly four")

    contradiction = base_model()
    contradiction["narrative"]["executive_p1"] = "The AI leadership signal is -6.2 points above benchmark, which should be blocked as a contradictory signed direction."
    assert_has_issue("signed contradiction", contradiction, "signed benchmark-direction contradiction")

    placeholder = base_model()
    placeholder["narrative"]["hero_p"] = "[DEV PLACEHOLDER: rewrite this section with AI-ready leadership insight before client use.]"
    assert_has_issue("placeholder", placeholder, "placeholder")



def test_function_focus_area_contract(tmp: Path) -> None:
    model = base_model()
    rows = model["heatmaps"]["function"]
    if function_focus_count(rows) != 1:
        raise AssertionError("synthetic functional rows should produce one Focus Area row")
    if focus_row_indexes(rows, "function") != {0}:
        raise AssertionError("Python should choose the first functional row as the Focus Area")

    src = write_model(tmp, "focus_area", model)
    out = tmp / "focus_area.html"
    result = run([sys.executable, str(SCRIPTS / "render_report.py"), str(src), "--out", str(out)])
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    html = out.read_text(encoding="utf-8")
    if html.count('class="function-opportunity-label"') != 1:
        raise AssertionError("functional Focus Area pill should render exactly once")
    if html.count('<tr class="priority-row priority-first priority-last"') < 1:
        raise AssertionError("functional Focus Area row should include first/last priority row classes")

    one_row = copy.deepcopy(model)
    one_row["heatmaps"]["function"] = [rows[0]]
    src = write_model(tmp, "focus_area_one_row", one_row)
    out = tmp / "focus_area_one_row.html"
    result = run([sys.executable, str(SCRIPTS / "render_report.py"), str(src), "--out", str(out)])
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    html = out.read_text(encoding="utf-8")
    if 'class="function-opportunity-label"' in html:
        raise AssertionError("single functional subgroup should not render a Focus Area pill")


def test_gap_extremes_render(tmp: Path) -> None:
    positive = set_responsibility_gaps(base_model(), [6.0, 5.0, 4.0, 3.0, 2.0, 1.0])
    assert_no_issues("all-positive gap model", positive)
    src = write_model(tmp, "all_positive", positive)
    out = tmp / "all_positive.html"
    result = run([sys.executable, str(SCRIPTS / "render_report.py"), str(src), "--out", str(out)])
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    html = out.read_text(encoding="utf-8")
    if "outperforms the AI-Ready Leader benchmark" not in html:
        raise AssertionError("all-positive model should render the outperforming benchmark heading")

    negative = set_responsibility_gaps(base_model(), [-1.0, -2.0, -3.0, -4.0, -5.0, -6.0])
    assert_no_issues("all-negative gap model", negative)
    src = write_model(tmp, "all_negative", negative)
    out = tmp / "all_negative.html"
    result = run([sys.executable, str(SCRIPTS / "render_report.py"), str(src), "--out", str(out)])
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    html = out.read_text(encoding="utf-8")
    if "trails the AI-Ready Leader benchmark overall" not in html:
        raise AssertionError("all-negative model should render the trailing benchmark heading")
    if "Relative Strength:" not in html:
        raise AssertionError("all-negative model should use Relative Strength rather than Largest Advantage")


def test_empty_heatmap_sections_render_limited_copy(tmp: Path) -> None:
    model = base_model()
    model["heatmaps"] = {"function": [], "level": [], "region": []}
    for field in list(model["narrative"].keys()):
        if "_meaning_" in field:
            del model["narrative"][field]
    assert_no_issues("empty heatmap sections", model)
    needed = required_narrative_fields(model)
    if any("_meaning_" in field for field in needed):
        raise AssertionError("heatmap meaning fields should not be required when all heatmap sections are empty")
    src = write_model(tmp, "empty_heatmaps", model)
    out = tmp / "empty_heatmaps.html"
    result = run([sys.executable, str(SCRIPTS / "render_report.py"), str(src), "--out", str(out)])
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    html = out.read_text(encoding="utf-8")
    for text in [
        "Function data are not available for benchmark comparison",
        "Job level data are not available for benchmark comparison",
        "Region data are not available for benchmark comparison",
    ]:
        if text not in html:
            raise AssertionError(f"missing deterministic limited-data copy: {text}")
    if '<div class="heat-takeaways"' in html:
        raise AssertionError("empty heatmap sections should not render LLM-authored heatmap takeaway cards")


def test_external_source_contract_and_rendering(tmp: Path) -> None:
    no_url = base_model()
    no_url["external_context"]["sources"] = []
    assert_has_issue("AI summary without URL-backed source", no_url, "no URL-backed")

    missing_title = base_model()
    missing_title["external_context"]["sources"] = [{"url": "https://example.com/ai", "purpose": "AI strategy context"}]
    assert_has_issue("external source missing title", missing_title, "title/name/label")

    missing_purpose = base_model()
    missing_purpose["external_context"]["sources"] = [{"title": "Example AI source", "url": "https://example.com/ai"}]
    assert_has_issue("external source missing purpose", missing_purpose, "purpose/context")

    model = base_model()
    model["external_context"]["sources"] = [
        {"title": "Example AI strategy page", "url": "https://example.com/ai", "purpose": "AI strategy context"},
        {"title": "Duplicate source", "url": "https://example.com/ai", "purpose": "Duplicate should be suppressed"},
    ]
    assert_no_issues("external source rendering model", model)
    src = write_model(tmp, "external_sources", model)
    out = tmp / "external_sources.html"
    result = run([sys.executable, str(SCRIPTS / "render_report.py"), str(src), "--out", str(out)])
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    html = out.read_text(encoding="utf-8")
    if 'id="external-context-sources"' not in html:
        raise AssertionError("external context source section should render when URL-backed sources are present")
    if html.count('href="https://example.com/ai"') != 1:
        raise AssertionError("external source URLs should be deduplicated by URL")
    if "Example AI strategy page" not in html or "AI strategy context" not in html:
        raise AssertionError("external source title and purpose should render")


def test_render_cli_requires_final_narrative(tmp: Path) -> None:
    draft = base_model()
    draft["narrative_status"] = "draft"
    src = write_model(tmp, "draft_render", draft)
    out = tmp / "draft_render.html"
    result = run([sys.executable, str(SCRIPTS / "render_report.py"), str(src), "--out", str(out)])
    if result.returncode == 0:
        raise AssertionError("render_report should block non-final narrative without the development override")
    if "render blocked" not in result.stderr:
        raise AssertionError("render_report should clearly explain that final validation blocked rendering")

    placeholder = base_model()
    placeholder["narrative"]["hero_p"] = "[DEV PLACEHOLDER: rewrite this section with AI-ready leadership insight before client use.]"
    src = write_model(tmp, "placeholder_render", placeholder)
    out = tmp / "placeholder_render.html"
    result = run([sys.executable, str(SCRIPTS / "render_report.py"), str(src), "--out", str(out)])
    if result.returncode == 0:
        raise AssertionError("render_report should block placeholder narrative in final mode")
    if "placeholder" not in result.stderr.lower():
        raise AssertionError("render_report should surface placeholder narrative validation issues")


def test_ai_operator_issue_codes(tmp: Path) -> None:
    draft = base_model()
    draft["narrative_status"] = "draft"
    codes = {issue["code"] for issue in validate_model_issues(draft, strict=True)}
    if "RENDER_NARRATIVE_NOT_FINAL" not in codes:
        raise AssertionError(f"draft model should emit RENDER_NARRATIVE_NOT_FINAL, got {codes}")

    sourced = base_model()
    sourced["external_context"]["sources"] = []
    codes = {issue["code"] for issue in validate_model_issues(sourced, strict=True)}
    if "SOURCE_MISSING_URL" not in codes:
        raise AssertionError(f"missing external source should emit SOURCE_MISSING_URL, got {codes}")

    label_led = base_model()
    label_led["narrative"]["executive_p2"] = (
        "Sustain the Vision, Take Decisive Action, and Scale for Impact are the strongest signals, "
        "which makes the narrative too label-led for an AI-ready leadership report."
    )
    src = write_model(tmp, "label_led", label_led)
    result = run([sys.executable, str(SCRIPTS / "lint_narrative_labels.py"), str(src), "--json"])
    if result.returncode == 0:
        raise AssertionError("label-led narrative should fail lint")
    payload = json.loads(result.stdout)
    codes = {issue.get("code") for issue in payload.get("issues", [])}
    if "STYLE_LABEL_LED" not in codes:
        raise AssertionError(f"label-led narrative should emit STYLE_LABEL_LED, got {codes}")
    for issue in payload.get("issues", []):
        if issue.get("code") and not issue.get("action"):
            raise AssertionError(f"issue code {issue.get('code')} should include an AI-operator action")


def test_typography_contract_restored(tmp: Path) -> None:
    model = base_model()
    src = write_model(tmp, "typography", model)
    out = tmp / "typography.html"
    result = run([sys.executable, str(SCRIPTS / "render_report.py"), str(src), "--out", str(out)])
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    html = out.read_text(encoding="utf-8")

    checks = [
        (".airl-explainer-section p", "font-size", "16px"),
        ("section.benchmark-section > p.lede", "font-size", "16px"),
        (".about-data-section .pie-legend span", "font-size", "11.5px"),
        (".about-data-section .year-bars div", "font-size", "11.5px"),
        (".about-data-section .level-bars div", "font-size", "11.5px"),
        (".about-data-section .year-bars b", "font-size", "11.5px"),
        (".about-data-section .level-bars b", "font-size", "11.5px"),
        (".about-data-section .level-bars div", "grid-template-columns", "128px 1fr 38px"),
                        (".about-data-section .type-legend", "grid-template-columns", "1fr"),
        (".about-data-section .region-legend", "grid-template-columns", "repeat(2, minmax(0, 1fr))"),
                        (".about-data-section .demo-dates .demo-date-metric > b:not(.total-count)", "font-size", "20px"),
        ("section.actions .section-kicker", "color", "#b8f4df"),
        ("section.actions .action-title", "color", "#fff"),
        ("section.actions .action", "background", "rgba(255,255,255,.08)"),
        (".header-footnote ul", "margin", "8px 0 0 18px"),
        (".header-footnote li", "margin", "5px 0"),
        (".external-sources p", "font-size", "13px"),
        (".external-sources a", "color", "var(--kf-forest, #00634f)"),
        (".airl-explainer-button", "background", "var(--kf-forest, #00634f)"),
        (".airl-explainer-button", "padding", "10px 16px"),
        (".underlying-signal-section .signals-score-footnote", "font-size", "12px"),
        (".underlying-signal-section .signals-score-footnote", "line-height", "1.4"),
    ]
    for selector, prop, value in checks:
        assert_css_property(html, selector, prop, value)

    if re.search(r"\.demo-panel\s+\.region-legend\s+span\s*\{[^}]*font-size\s*:\s*10\.6px", html, re.S):
        raise AssertionError("region legend should no longer carry a region-only font-size shrink")
    if 'class="legend-item"' in html or 'class="legend-pct"' in html:
        raise AssertionError("pie legends should use the simple inline legend treatment, not structured aligned percentage markup")
    fixed_signal_note = "Gap values are percentage-point differences between client scores and the selected benchmark. Positive values indicate scores above the benchmark; larger values indicate a stronger relative advantage."
    if fixed_signal_note not in html:
        raise AssertionError("Leadership Signals should render the fixed benchmark-independent score-reading note")
    if "client score and the AI-Ready Leader benchmark" in html:
        raise AssertionError("Leadership Signals score-reading note should not inject a client name or fixed benchmark name")


def test_heatmap_and_participant_summary_polish(tmp: Path) -> None:
    model = base_model()
    src = write_model(tmp, "visual_polish", model)
    out = tmp / "visual_polish.html"
    result = run([sys.executable, str(SCRIPTS / "render_report.py"), str(src), "--out", str(out)])
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    html = out.read_text(encoding="utf-8")

    if "<h3>Coverage</h3>" not in html:
        raise AssertionError("participant/date card should render the single-line Coverage title")
    if "<h3>Participant summary</h3>" in html:
        raise AssertionError("participant/date card should use the shorter Coverage title")
    if '<div class="section-kicker">Job Level patterns</div>' not in html:
        raise AssertionError("level heatmap should use the Job Level patterns kicker")
    if '<div class="section-kicker">Population patterns</div>' in html:
        raise AssertionError("level heatmap should no longer use generic Population patterns kicker")

    # Keep these semantic: the contract is the active property on the owning selector,
    # not exact source formatting or declaration order.
    css_checks = [
        ("section.panel.heat .heat-table th:first-child", "text-align", "left"),
        ("section.panel.heat .heat-table th:not(:first-child)", "text-align", "center"),
        (".about-data-section .demo-dates h3", "margin-bottom", "12px"),
        (".about-data-section .demo-dates", "gap", "0"),
        (".about-data-section .demo-dates .demo-date-metric", "margin", "0 0 15px"),
    ]
    for selector, prop, value in css_checks:
        assert_css_property(html, selector, prop, value)


def test_single_row_copy_uses_workbook_comparison_language(tmp: Path) -> None:
    model = base_model()
    model["heatmaps"]["function"] = [heat_row("Only Function", 2.0)]
    model["heatmaps"]["level"] = [heat_row("Only Level", 2.0)]
    model["heatmaps"]["region"] = [heat_row("Only Region", 2.0)]
    for field in list(model["narrative"].keys()):
        if "_meaning_" in field:
            del model["narrative"][field]
    src = write_model(tmp, "single_row_copy", model)
    out = tmp / "single_row_copy.html"
    result = run([sys.executable, str(SCRIPTS / "render_report.py"), str(src), "--out", str(out)])
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    html = out.read_text(encoding="utf-8")
    if "enough assessed participants" in html:
        raise AssertionError("single-row heatmap copy should not imply the renderer applied an N-size threshold")
    for phrase in [
        "only function with comparison data available in this workbook",
        "only job level with comparison data available in this workbook",
        "only region with comparison data available in this workbook",
    ]:
        if phrase not in html:
            raise AssertionError(f"missing revised single-row comparison copy: {phrase}")


def test_dev_render_override_allows_smoke_render(tmp: Path) -> None:
    draft = base_model()
    draft["narrative_status"] = "draft"
    src = write_model(tmp, "draft_dev_render", draft)
    out = tmp / "draft_dev_render.html"
    result = run([sys.executable, str(SCRIPTS / "render_report.py"), str(src), "--out", str(out), "--allow-default-narrative"])
    if result.returncode != 0:
        raise AssertionError("development render override should allow smoke rendering: " + (result.stderr or result.stdout))
    if not out.exists():
        raise AssertionError("development render override did not create an HTML output")


def test_external_url_and_high_risk_fact_guards(tmp: Path) -> None:
    malformed = base_model()
    malformed["external_context"]["sources"] = [{"title": "Malformed", "url": "example.com/ai", "purpose": "AI strategy context"}]
    codes = {issue["code"] for issue in validate_model_issues(malformed, strict=True)}
    if "SOURCE_INVALID_URL" not in codes:
        raise AssertionError(f"malformed source URL should emit SOURCE_INVALID_URL, got {codes}")
    if "SOURCE_MISSING_URL" not in codes:
        raise AssertionError(f"malformed source URL should not satisfy URL-backed source requirements, got {codes}")

    high_risk = base_model()
    high_risk["external_context"]["ai_strategy_summary"] = ""
    high_risk["external_context"]["sources"] = []
    high_risk["narrative"]["executive_p2"] = (
        "The client has an AI partnership with Example Technology Partner, which creates a high-risk external fact pattern "
        "that should require source grounding before client-ready rendering."
    )
    codes = {issue["code"] for issue in validate_model_issues(high_risk, strict=True)}
    if "SOURCE_HIGH_RISK_FACT" not in codes:
        raise AssertionError(f"unsupported high-risk external facts should emit SOURCE_HIGH_RISK_FACT, got {codes}")


def test_all_positive_watch_language_guard(tmp: Path) -> None:
    model = set_responsibility_gaps(base_model(), [6.0, 5.0, 4.0, 3.0, 2.0, 1.0])
    model["narrative"]["watch_narrative"] = "This weakness sits below benchmark and should be treated as a low-readiness deficit."
    codes = {issue["code"] for issue in validate_model_issues(model, strict=True)}
    if "STYLE_OVERSTATEMENT" not in codes:
        raise AssertionError(f"all-positive watch-area overstatement should emit STYLE_OVERSTATEMENT, got {codes}")




def test_external_context_evidence_ledger_contract(tmp: Path) -> None:
    model = base_model()
    model["external_context"]["sources"] = []
    model["external_context"]["vetted_context_bullets"] = [
        {
            "claim": "The client publicly describes AI-enabled transformation as a current strategic priority.",
            "source_title": "Example AI strategy page",
            "source_url": "https://example.com/strategy",
            "use": "AI strategy evidence",
        }
    ]
    assert_no_issues("valid evidence ledger without duplicate sources", model)
    src = write_model(tmp, "evidence_ledger", model)
    out = tmp / "evidence_ledger.html"
    result = run([sys.executable, str(SCRIPTS / "render_report.py"), str(src), "--out", str(out)])
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    html = out.read_text(encoding="utf-8")
    if "Example AI strategy page" not in html or "AI strategy evidence" not in html:
        raise AssertionError("vetted evidence-ledger source should render in External Context Sources")
    if "The client publicly describes AI-enabled transformation" in html:
        raise AssertionError("vetted evidence-ledger claims should not print as report prose in the source list")

    incomplete = base_model()
    incomplete["external_context"]["sources"] = []
    incomplete["external_context"]["vetted_context_bullets"] = [
        {"claim": "Too short", "source_url": "example.com/bad"}
    ]
    codes = {issue["code"] for issue in validate_model_issues(incomplete, strict=True)}
    if "SOURCE_LEDGER_INCOMPLETE" not in codes:
        raise AssertionError(f"incomplete vetted bullets should emit SOURCE_LEDGER_INCOMPLETE, got {codes}")
    if "SOURCE_INVALID_URL" not in codes:
        raise AssertionError(f"malformed vetted bullet URL should emit SOURCE_INVALID_URL, got {codes}")

    high_risk = base_model()
    high_risk["external_context"]["ai_strategy_summary"] = ""
    high_risk["external_context"]["sources"] = []
    high_risk["external_context"]["vetted_context_bullets"] = [
        {
            "claim": "The client announced an AI partnership with Example Technology Partner as part of a transformation program.",
            "source_title": "Example partnership source",
            "source_url": "https://example.com/partnership",
            "use": "AI partnership evidence",
        }
    ]
    high_risk["narrative"]["executive_p2"] = (
        "The client has an AI partnership with Example Technology Partner, so leaders need to connect Human + AI adoption "
        "to practical change routines and execution discipline."
    )
    codes = {issue["code"] for issue in validate_model_issues(high_risk, strict=True)}
    if "SOURCE_HIGH_RISK_FACT" in codes:
        raise AssertionError(f"valid vetted evidence should satisfy high-risk external fact grounding, got {codes}")


def synthetic_workbook(path: Path) -> None:
    demo_rows = []
    for i in range(30):
        demo_rows.append({
            "CIQUltimateParentName": "Example Enterprise plc",
            "AssmtKey": f"A{i:03d}",
            "CompletedYear": 2025,
            "CompletedDate": "2025-06-01",
            "Region": "North America" if i < 15 else "Europe",
            "FunctionName": "Operations" if i < 15 else "Technology",
            "LevelName": "Executive" if i < 10 else "Senior Leader",
            "AssessmentType": "leadership_assessment",
        })
    data_rows = []
    aliases = {
        ORDER[0]: ORDER[0],
        ORDER[1]: ORDER[1],
        ORDER[2]: "Scale For Impact",
        ORDER[3]: ORDER[3].replace("'", "’"),
        ORDER[4]: "Champion Learning & Unlearning",
        ORDER[5]: ORDER[5],
    }
    for idx, canonical in enumerate(ORDER):
        display_name = aliases[canonical]
        score = 70 + idx
        bench = 65
        data_rows.append({
            "CutType": "Overall", "CutName": "Overall", "DataType": "Composite", "KF4D_Code": f"C{idx}",
            "Construct": "Composite", "CompositeName": display_name, "ParticipantCount": 30,
            "TargetHitPct": score, "BenchmarkPct": bench, "GapVsBenchmark": score - bench,
        })
    data_rows.append({
        "CutType": "Overall", "CutName": "Overall", "DataType": "Overall", "KF4D_Code": "OVERALL",
        "Construct": "Overall", "CompositeName": "Overall", "ParticipantCount": 30,
        "TargetHitPct": 72, "BenchmarkPct": 66, "GapVsBenchmark": 6,
    })
    construct_rows = [
        ("CP", "Composure", "Address Fears"),
        ("COU", "Courage", "Address Fears"),
        ("CR", "Credibility", "Address Fears"),
        ("ITR", "Instills Trust", "Address Fears"),
        ("AD", "Adaptability", "Champion Learning and Unlearning"),
    ]
    for idx, (code, construct, composite_name) in enumerate(construct_rows):
        score = 74 - idx
        bench = 67
        data_rows.append({
            "CutType": "Overall", "CutName": "Overall", "DataType": "Construct", "KF4D_Code": code,
            "Construct": construct, "CompositeName": composite_name, "ParticipantCount": 30,
            "TargetHitPct": score, "BenchmarkPct": bench, "GapVsBenchmark": score - bench,
        })
    with pd.ExcelWriter(path) as writer:
        pd.DataFrame(demo_rows).to_excel(writer, sheet_name="demographics", index=False)
        pd.DataFrame(data_rows).to_excel(writer, sheet_name="data", index=False)


def test_workbook_alias_normalization(tmp: Path) -> None:
    workbook = tmp / "alias_workbook.xlsx"
    synthetic_workbook(workbook)
    result = run([sys.executable, str(SCRIPTS / "validate_workbook.py"), str(workbook)])
    if result.returncode != 0:
        raise AssertionError(result.stdout + result.stderr)
    model_path = tmp / "alias_model.json"
    result = run([sys.executable, str(SCRIPTS / "build_content_model.py"), str(workbook), "--out", str(model_path)])
    if result.returncode != 0:
        raise AssertionError(result.stdout + result.stderr)
    model = json.loads(model_path.read_text(encoding="utf-8"))
    built = [item["responsibility"] for item in model["metrics"]["responsibilities"]]
    if built != list(ORDER):
        raise AssertionError(f"responsibility aliases did not normalize to canonical order: {built}")


def test_build_content_model_missing_responsibility_guard(tmp: Path) -> None:
    workbook = tmp / "missing_responsibility.xlsx"
    synthetic_workbook(workbook)
    demo = pd.read_excel(workbook, sheet_name="demographics")
    data = pd.read_excel(workbook, sheet_name="data")
    data = data[~((data["DataType"] == "Composite") & (data["CompositeName"] == ORDER[-1]))].copy()
    with pd.ExcelWriter(workbook) as writer:
        demo.to_excel(writer, sheet_name="demographics", index=False)
        data.to_excel(writer, sheet_name="data", index=False)
    model_path = tmp / "missing_responsibility_model.json"
    result = run([sys.executable, str(SCRIPTS / "build_content_model.py"), str(workbook), "--out", str(model_path)])
    if result.returncode == 0:
        raise AssertionError("build_content_model should fail clearly when required responsibility rows are missing")
    if "missing required AI-Ready Leader responsibilities" not in (result.stderr + result.stdout):
        raise AssertionError("missing responsibility failure should include a clear local guard message")


def test_dynamic_css_ownership_boundary(tmp: Path) -> None:
    render_source = (SCRIPTS / "render_report.py").read_text(encoding="utf-8")
    template_source = (ROOT / "assets" / "report_template.html").read_text(encoding="utf-8")
    static_selectors = [
        ".external-sources",
        ".airl-explainer-section",
        ".airl-explainer-button",
        "section.actions .action-grid",
        ".header-footnote ul",
    ]
    css_block_start = render_source.find("css = f")
    if css_block_start < 0:
        raise AssertionError("render_report.py should still define dynamic CSS explicitly")
    dynamic_region = render_source[css_block_start:render_source.find("jump_links", css_block_start)]
    active_template_css = strip_css_comments(template_source)
    for selector in static_selectors:
        if selector in dynamic_region:
            raise AssertionError(f"static template selector should not be injected by Python: {selector}")
        if selector not in active_template_css:
            raise AssertionError(f"static template selector missing from active report_template.html CSS: {selector}")
    if "Dynamic-adjacent static component styles" in template_source:
        comment_pos = template_source.index("Dynamic-adjacent static component styles")
        first_selector_pos = template_source.find(".demo-panel .type-legend", comment_pos)
        comment_close_pos = template_source.find("*/", comment_pos)
        if first_selector_pos < 0 or comment_close_pos < 0 or comment_close_pos > first_selector_pos:
            raise AssertionError("dynamic-adjacent static CSS maintenance comment must close before selectors")
    if dynamic_region.count("!important") > 5:
        raise AssertionError("Python-injected CSS should remain limited to workbook-driven values")



def test_fixed_high_engagement_benchmark_reference(tmp: Path) -> None:
    workbook = tmp / "fixed_benchmark.xlsx"
    synthetic_workbook(workbook)
    demo = pd.read_excel(workbook, sheet_name="demographics")
    data = pd.read_excel(workbook, sheet_name="data")
    # Client workbooks no longer need secondary benchmark columns.
    data = data.drop(columns=[c for c in ["Benchmark2Pct", "GapVsBenchmark2"] if c in data.columns])
    with pd.ExcelWriter(workbook) as writer:
        demo.to_excel(writer, sheet_name="demographics", index=False)
        data.to_excel(writer, sheet_name="data", index=False)
    model_path = tmp / "fixed_benchmark_model.json"
    result = run([sys.executable, str(SCRIPTS / "build_content_model.py"), str(workbook), "--out", str(model_path)])
    if result.returncode != 0:
        raise AssertionError(result.stdout + result.stderr)
    model = json.loads(model_path.read_text(encoding="utf-8"))
    ids = [b.get("id") for b in model.get("benchmarks", [])]
    if ids != ["overall", "high_engagement"]:
        raise AssertionError(f"expected canonical benchmark ids, got {ids}")
    high = model["benchmark_views"]["high_engagement"]
    if abs(float(high["metrics"]["overall_average_benchmark"]) - 58.3275063973137) > 1e-9:
        raise AssertionError("fixed High Engagement overall benchmark did not load from reference")
    sustain = high["metrics"]["responsibilities"][0]
    if abs(float(sustain["benchmark_pct"]) - 52.5165682080511) > 1e-9:
        raise AssertionError("fixed responsibility benchmark did not map correctly")
    expected_gap = float(sustain["target_hit_pct"]) - float(sustain["benchmark_pct"])
    if abs(float(sustain["gap_vs_benchmark"]) - expected_gap) > 1e-9:
        raise AssertionError("High Engagement gap should be deterministically calculated from client score - fixed benchmark")


def test_dual_benchmark_toggle_rendering(tmp: Path) -> None:
    model = base_model()
    overall_view = {
        "benchmark": {"id": "overall", "label": "Overall Benchmark", "short_label": "Overall", "pct_column": "BenchmarkPct", "gap_column": "GapVsBenchmark", "is_default": True, "participant_count_approx": 340000, "organization_count_approx": 3000, "description": "Average AI-Ready Leader results across Korn Ferry Assess, global and cross-industry.", "methodology_note": "", "footnote_context": "The Overall Benchmark reflects average AI-Ready Leader results from approximately 340,000 participants across 3,000 organizations in Korn Ferry's global, cross-industry assessment database."},
        "metrics": copy.deepcopy(model["metrics"]),
        "heatmaps": copy.deepcopy(model["heatmaps"]),
    }
    high_metrics = copy.deepcopy(model["metrics"])
    high_metrics["average_gap_vs_benchmark"] = -6.0
    for record in high_metrics["responsibilities"]:
        record["benchmark_pct"] = record["target_hit_pct"] + 6.0
        record["gap_vs_benchmark"] = -6.0
    high_metrics["largest_advantage"] = high_metrics["responsibilities"][0]
    high_metrics["largest_advantage_label"] = "Relative Strength"
    high_metrics["watch_area"] = high_metrics["responsibilities"][-1]
    high_metrics["watch_area_context"] = "below_benchmark"
    high_heatmaps = copy.deepcopy(model["heatmaps"])
    for rows in high_heatmaps.values():
        for row in rows:
            row["overall_gap"] = float(row["overall_gap"]) - 10
            for cell in row["cells"]:
                cell["gap"] = float(cell["gap"]) - 10
    model["benchmarks"] = [overall_view["benchmark"], {"id": "high_engagement", "label": "High Engagement Benchmark", "short_label": "High Engagement", "pct_column": "Benchmark2Pct", "gap_column": "GapVsBenchmark2", "is_default": False, "participant_count_approx": 60000, "organization_count_approx": 2000, "description": "AI-Ready Leader results for the top 25% of participants on Work Engagement.", "methodology_note": "Work Engagement is used as a proxy for job performance.", "footnote_context": "The High Engagement Benchmark reflects AI-Ready Leader results from approximately 60,000 participants across 2,000 organizations in the top 25% on Work Engagement. High engagement provides a useful aspirational comparison because it reflects leaders who are more strongly connected to their work and organization. Comparing with this population helps indicate whether the client's leadership profile resembles patterns seen among more highly engaged assessed individuals. Work Engagement reflects satisfaction, emotional investment, and willingness to expend discretionary effort for the organization and is used here as a proxy for job performance."}]
    model["benchmark_views"] = {
        "overall": overall_view,
        "high_engagement": {"benchmark": model["benchmarks"][1], "metrics": high_metrics, "heatmaps": high_heatmaps},
    }
    model["active_benchmark_id"] = "overall"
    # Shared narrative remains valid, while benchmark-specific narrative can override later in production use.
    path = write_model(tmp, "dual_benchmark", model)
    out = tmp / "dual_benchmark.html"
    result = run([sys.executable, str(SCRIPTS / "render_report.py"), str(path), "--out", str(out)])
    if result.returncode != 0:
        raise AssertionError(result.stderr + result.stdout)
    html = out.read_text(encoding="utf-8")
    if 'data-benchmark-toggle="overall"' not in html or 'data-benchmark-toggle="high_engagement"' not in html:
        raise AssertionError("dual-benchmark reports should render sticky-nav benchmark toggle buttons")
    if html.count('data-benchmark-view="overall"') < 6 or html.count('data-benchmark-view="high_engagement"') < 6:
        raise AssertionError("benchmark-sensitive sections should render paired benchmark views")
    if "Active benchmark:" in html or "benchmark-view-badge" in html:
        raise AssertionError("section-level active benchmark badges should not render")
    if 'data-benchmark-view="high_engagement" hidden' not in html:
        raise AssertionError("non-default benchmark view should be hidden until toggled")
    if "High Engagement" not in html or ">Benchmark</span>" not in html:
        raise AssertionError("sticky toggle should expose a compact Benchmark label above concise benchmark labels")
    if "Benchmark context" in html or "benchmark-context" in html:
        raise AssertionError("Benchmark Comparison should not render a separate Benchmark Context block")
    if html.count("approximately 340,000 participants") != 1 or html.count("approximately 60,000 participants") != 1:
        raise AssertionError("each benchmark view should carry only its own deterministic context in its How to read footnote")
    if "The Overall Benchmark reflects average AI-Ready Leader results" not in html:
        raise AssertionError("Overall benchmark context should be appended to the Overall How to read footnote")
    if "The High Engagement Benchmark reflects AI-Ready Leader results" not in html or "useful aspirational comparison" not in html or "more strongly connected to their work and organization" not in html or "Work Engagement reflects satisfaction" not in html or "used here as a proxy for job performance" not in html:
        raise AssertionError("High Engagement rationale, context, and methodology should be appended to the selected How to read footnote")
    if html.count('class="gap-footnote benchmark-score-footnote"') != 2:
        raise AssertionError("each benchmark view should render one selected-benchmark How to read footnote")
    if "compared with the selected <b>Overall or High Engagement benchmark</b>" not in html:
        raise AssertionError("Data interpretation note should recognize either selected benchmark")
    if html.count('id="follow-up-opportunities"') != 1:
        raise AssertionError("follow-up opportunities should render once as a shared section")
    if 'Gap values compare against the active benchmark view' in html or 'above the active benchmark' in html:
        raise AssertionError("benchmark and heatmap footnotes should remain static")
    if 'grid-template-areas: "logo title title" "logo links toggle"' not in html:
        raise AssertionError("desktop sticky nav should align identity, section navigation, and benchmark control within the report rail")
    if '.benchmark-toggle.is-visible' not in html or "benchmarkControl.classList.toggle('is-visible', navStuck && navLinksVisible)" not in html:
        raise AssertionError("inline benchmark control should appear only in the sticky section-navigation state")
    if 'class="benchmark-toggle-track"' not in html:
        raise AssertionError("only the benchmark buttons should sit inside the recessed toggle track")
    if '.benchmark-toggle-button.active' not in html or 'background: #b8f4df !important' not in html:
        raise AssertionError("active benchmark button should use the mint state distinct from navigation pills")
    if 'grid-area: toggle !important' not in html or 'margin: 0 !important' not in html:
        raise AssertionError("benchmark control should remain inline and align directly to the report content rail")
    if 'min-height: 42px !important' not in html or 'padding: 8px 0 0 !important' not in html or 'justify-content: center !important' not in html:
        raise AssertionError("benchmark button centers should align with the section-navigation pill centers")
    if 'position: absolute !important' not in html or 'top: 0 !important' not in html or 'transform: translateX(-50%) !important' not in html:
        raise AssertionError("Benchmark label should sit above the track without shifting the button row downward")
    if 'min-height: 24px !important' not in html or 'padding: 5px 11px !important' not in html:
        raise AssertionError("inline benchmark buttons should remain slightly smaller than navigation pills")
    if 'font-size: 12px !important' not in html:
        raise AssertionError("benchmark selector typography should match the 12px section-navigation text size")
    if "Overall AI-Ready Leader result for the assessed" not in html:
        raise AssertionError("Benchmark Comparison overall-row definition should describe the database aggregate result")
    if '@media (max-width:1500px)' not in html or '@media (max-width:1280px)' not in html or '@media (max-width:1040px)' not in html or '@media (max-width:680px)' not in html:
        raise AssertionError("sticky navigation should use coordinated structural breakpoints before controls can clip")
    if 'grid-template-areas: "logo title title" "links links toggle" !important' not in html:
        raise AssertionError("medium-width nav should reclaim the logo column on the controls row while keeping benchmark inline")
    if 'grid-template-areas: "logo title" "links links" "toggle toggle" !important' not in html:
        raise AssertionError("benchmark control should move to its own row only once the combined control row becomes crowded")
    if 'flex-wrap: wrap !important' not in html or 'overflow: visible !important' not in html:
        raise AssertionError("section navigation should wrap cleanly instead of clipping or hiding links at constrained widths")
    if "window.dispatchEvent(new Event('benchmarkchange'))" not in html:
        raise AssertionError("benchmark switching should trigger Focus Area geometry recalculation")

    from lint_narrative_labels import lint_low_target_construct_direction
    low_target_model = {"narrative": {"signals_high_text": "Leaders show high Structure and enough Structure to handle ambiguity."}}
    low_target_issues = lint_low_target_construct_direction(low_target_model)
    if not low_target_issues or low_target_issues[0].get("code") != "STYLE_LOW_TARGET_CONSTRUCT":
        raise AssertionError("low-target Structure/Balance direction reversals should be linted")
    safe_low_target_model = {"narrative": {"signals_high_text": "Leaders show lower reliance on routine and greater comfort operating through ambiguity."}}
    if lint_low_target_construct_direction(safe_low_target_model):
        raise AssertionError("behaviorally translated low-target construct interpretation should pass lint")
    if "pill.style.setProperty('--focus-pill-left', '-30px')" not in html:
        raise AssertionError("functional Focus Area pill should use the shared table-anchored horizontal position")
    if '.about-data-section .type-legend' not in html or 'justify-self: start !important' not in html:
        raise AssertionError("Assessment Type legend should remain left-aligned")


def test_dual_benchmark_narrative_rules_are_standalone(tmp: Path):
    rules = (ROOT / "references" / "narrative_rules.md").read_text(encoding="utf-8")
    required = [
        "complete standalone client story",
        "Treat the selected benchmark as **evidence**, not as the narrative subject.",
        "Do not call the High Engagement Benchmark a `stretch benchmark`",
        "Never insert an actual client name into narrative-rule examples",
    ]
    for text in required:
        if text not in rules:
            raise AssertionError(f"missing dual-benchmark standalone narrative rule: {text}")
    # Narrative-rule examples must remain generic and must not inherit the smoke-test client name.
    for forbidden_client_name in ("Sample Client", "Example Client"):
        if forbidden_client_name in rules:
            raise AssertionError("narrative rules must not contain a smoke-test client name")
    bad = base_model()
    bad["benchmark_narratives"] = {"high_engagement": {"executive_h2": "Against a higher aspiration, the stretch benchmark shifts the question toward consistency."}}
    issues = lint_benchmark_referential_framing(bad)
    if not issues or issues[0].get("code") != "STYLE_BENCHMARK_FRAMING":
        raise AssertionError("legacy stretch/higher-bar framing should be linted in High Engagement narrative")


def test_about_data_responsive_reflow_contract(tmp: Path) -> None:
    template = (ROOT / "assets" / "report_template.html").read_text(encoding="utf-8")
    required = [
        "@media (max-width:1100px)",
        ".about-data-section .demo-panel",
        "grid-template-columns: repeat(2, minmax(0, 1fr)) !important",
        ".about-data-section .demo-level",
        "grid-column: 1 / -1 !important",
        "@media (max-width:760px)",
        "grid-template-columns: minmax(0, 1fr) !important",
        "grid-column: auto !important",
    ]
    for text in required:
        if text not in template:
            raise AssertionError(f"missing responsive demographic layout contract: {text}")


def main() -> int:
    tests = [
        test_full_model_renders,
        test_limited_heatmap_narrative_contract,
        test_narrative_escaping,
        test_final_validation_blocks_bad_narrative,
        test_function_focus_area_contract,
        test_gap_extremes_render,
        test_empty_heatmap_sections_render_limited_copy,
        test_external_source_contract_and_rendering,
        test_render_cli_requires_final_narrative,
        test_ai_operator_issue_codes,
        test_typography_contract_restored,
        test_about_data_responsive_reflow_contract,
        test_heatmap_and_participant_summary_polish,
        test_single_row_copy_uses_workbook_comparison_language,
        test_dev_render_override_allows_smoke_render,
        test_external_url_and_high_risk_fact_guards,
        test_all_positive_watch_language_guard,
        test_workbook_alias_normalization,
        test_build_content_model_missing_responsibility_guard,
        test_dynamic_css_ownership_boundary,
        test_external_context_evidence_ledger_contract,
        test_fixed_high_engagement_benchmark_reference,
        test_dual_benchmark_toggle_rendering,
        test_dual_benchmark_narrative_rules_are_standalone,
    ]
    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="airl_regression_") as tmp_dir:
        tmp = Path(tmp_dir)
        for test in tests:
            try:
                test(tmp)
                print(f"PASS {test.__name__}")
            except Exception as exc:
                print(f"FAIL {test.__name__}: {exc}")
                failures.append(f"{test.__name__}: {exc}")
    if failures:
        print("\nRegression harness failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"\nAll {len(tests)} regression tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
