#!/usr/bin/env python3
"""Validate finalized AIRL Pulse content models before rendering.

This script enforces the narrative contract that sits between deterministic
workbook processing and HTML rendering. It is intentionally stricter than the
workbook validator: a content model can be structurally valid but still not be
ready for a client report if narrative is missing, placeholder-like, or uses
unsourced external facts.

Exit code:
  0 = content model is ready to render
  1 = final narrative/content-model contract issues were found
  2 = usage or file errors
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from airl_benchmarks import benchmark_views, model_for_benchmark, narrative_for_benchmark
from airl_external_sources import external_evidence_sources, is_url_backed, normalized_external_sources, normalized_vetted_context_bullets, url_backed_sources


ISSUE_CATALOG = {
    "RENDER_NARRATIVE_NOT_FINAL": {
        "category": "render_blocking",
        "action": "Do not render a client-ready report; finish narrative fields and set narrative_status to final only after QA passes.",
    },
    "CONTRACT_MISSING_FIELD": {
        "category": "content_contract",
        "action": "Populate the missing narrative/content-model field or rebuild the content model if deterministic inputs are incomplete.",
    },
    "PLACEHOLDER_TEXT_BLOCKED": {
        "category": "render_blocking",
        "action": "Rewrite the placeholder or draft-like text with final client-ready narrative before rendering.",
    },
    "SOURCE_MISSING_URL": {
        "category": "source_grounding",
        "action": "Add at least one URL-backed external_context.sources item or remove unsupported external AI strategy claims.",
    },
    "SOURCE_MISSING_METADATA": {
        "category": "source_grounding",
        "action": "Add a concise title and purpose/context note to each URL-backed source.",
    },
    "SOURCE_INVALID_URL": {
        "category": "source_grounding",
        "action": "Replace malformed external source URLs with valid http(s) URLs or remove unsupported external context.",
    },
    "SOURCE_LEDGER_INCOMPLETE": {
        "category": "source_grounding",
        "action": "Complete each vetted_context_bullets item with a concise claim, source title, http(s) source URL, and use/purpose note, or remove the incomplete evidence bullet.",
    },
    "STYLE_HERO_IMPLICATION": {
        "category": "narrative_style",
        "action": "Rewrite the hero subtitle as a direct AI/Human + AI leadership implication, not methodology or report-description language.",
    },
    "STYLE_EXECUTIVE_ANCHOR": {
        "category": "narrative_style",
        "action": "Rewrite the executive narrative so it leads with insight and includes one concise benchmark or data anchor when required.",
    },
    "CONTRACT_FOLLOW_UP_COUNT": {
        "category": "content_contract",
        "action": "Provide exactly four client-ready follow-up recommendations.",
    },
    "STYLE_ACTION_ORIENTATION": {
        "category": "narrative_style",
        "action": "Add action-oriented leadership implications or follow-up guidance grounded in the observed pattern.",
    },
    "STYLE_SIGNED_GAP_CONTRADICTION": {
        "category": "narrative_style",
        "action": "Correct signed benchmark language so negative gaps are below benchmark and positive gaps are above benchmark.",
    },
    "SOURCE_HIGH_RISK_FACT": {
        "category": "source_grounding",
        "action": "Remove the unsupported external fact or add URL-backed source evidence.",
    },
    "CONTRACT_METRIC_LABEL": {
        "category": "content_contract",
        "action": "Rebuild or correct the deterministic metric label/context so it matches the score pattern.",
    },
    "STYLE_OVERSTATEMENT": {
        "category": "narrative_style",
        "action": "Temper the prose so it does not overstate non-positive or lowest-positive benchmark patterns.",
    },
    "VALIDATION_GENERAL": {
        "category": "content_contract",
        "action": "Inspect the flagged field, fix the content model or narrative, then rerun validation/lint before rendering.",
    },
}


def classify_issue_message(message: str) -> str:
    lower = message.lower()
    if "narrative_status" in lower:
        return "RENDER_NARRATIVE_NOT_FINAL"
    if "placeholder" in lower or "draft text" in lower:
        return "PLACEHOLDER_TEXT_BLOCKED"
    if "missing or too short" in lower:
        return "CONTRACT_MISSING_FIELD"
    if "high-risk external fact" in lower:
        return "SOURCE_HIGH_RISK_FACT"
    if "vetted_context_bullets" in lower and ("missing" in lower or "should include" in lower or "invalid" in lower):
        if "url" in lower and ("invalid" in lower or "http" in lower):
            return "SOURCE_INVALID_URL"
        return "SOURCE_LEDGER_INCOMPLETE"
    if "invalid external source url" in lower or "non-http" in lower or "malformed" in lower:
        return "SOURCE_INVALID_URL"
    if "no url-backed" in lower:
        return "SOURCE_MISSING_URL"
    if "title/name/label" in lower or "purpose/context" in lower:
        return "SOURCE_MISSING_METADATA"
    if "hero" in lower and ("human + ai" in lower or "subheading" in lower):
        return "STYLE_HERO_IMPLICATION"
    if "executive narrative" in lower and ("data anchor" in lower or "quantitative" in lower or "participant count" in lower or "human + ai" in lower):
        return "STYLE_EXECUTIVE_ANCHOR"
    if "exactly four" in lower:
        return "CONTRACT_FOLLOW_UP_COUNT"
    if "action-oriented" in lower:
        return "STYLE_ACTION_ORIENTATION"
    if "signed benchmark-direction contradiction" in lower:
        return "STYLE_SIGNED_GAP_CONTRADICTION"
    if "high-risk external fact" in lower:
        return "SOURCE_HIGH_RISK_FACT"
    if "largest_advantage_label" in lower:
        return "CONTRACT_METRIC_LABEL"
    if "must not overstate" in lower or "should acknowledge" in lower:
        return "STYLE_OVERSTATEMENT"
    return "VALIDATION_GENERAL"


def issue_record(message: str) -> dict[str, str]:
    code = classify_issue_message(message)
    meta = ISSUE_CATALOG.get(code, ISSUE_CATALOG["VALIDATION_GENERAL"])
    return {
        "code": code,
        "category": meta["category"],
        "message": message,
        "action": meta["action"],
    }


def format_issue(record: dict[str, str]) -> str:
    return f"[{record['code']}] {record['message']} | action: {record['action']}"

BASE_REQUIRED_NARRATIVE_FIELDS = [
    "hero_h1", "hero_p",
    "executive_h2", "executive_p1", "executive_p2", "commercial_implication",
    "largest_narrative", "watch_narrative",
    "story_h2", "story_card_1_title", "story_card_1_text", "story_card_2_title", "story_card_2_text",
    "story_toggle_1_title", "story_toggle_1_text", "story_toggle_2_title", "story_toggle_2_text",
    "story_toggle_3_title", "story_toggle_3_text", "story_toggle_4_title", "story_toggle_4_text",
    "signals_high_text", "signals_low_text",
]

HEATMAP_NARRATIVE_FIELDS = {
    "function": [
        "function_meaning_1_title", "function_meaning_1_text",
        "function_meaning_2_title", "function_meaning_2_text",
        "function_meaning_3_title", "function_meaning_3_text",
    ],
    "level": [
        "level_meaning_1_title", "level_meaning_1_text",
        "level_meaning_2_title", "level_meaning_2_text",
        "level_meaning_3_title", "level_meaning_3_text",
    ],
    "region": [
        "region_meaning_1_title", "region_meaning_1_text",
        "region_meaning_2_title", "region_meaning_2_text",
        "region_meaning_3_title", "region_meaning_3_text",
    ],
}


def required_narrative_fields(model: dict[str, Any]) -> list[str]:
    """Return narrative fields required for the sections that will render.

    Comparative heatmap interpretation cards render only when a subgroup section
    has at least two usable rows. For 0-1 rows, deterministic limited-data copy
    renders instead, so those LLM narrative fields are intentionally not required.
    """
    fields = list(BASE_REQUIRED_NARRATIVE_FIELDS)
    heatmaps = model.get("heatmaps", {}) or {}
    for section_type, section_fields in HEATMAP_NARRATIVE_FIELDS.items():
        if len(heatmaps.get(section_type, []) or []) >= 2:
            fields.extend(section_fields)
    return fields

PLACEHOLDER_PATTERNS = [
    re.compile(r"\[\s*(placeholder|replace|todo|draft)\b", re.I),
    re.compile(r"\bplaceholder\b|\btodo\b|\bto be written\b", re.I),
]

HIGH_RISK_EXTERNAL_FACT_PATTERNS = [
    ("currency or financial amount", re.compile(r"(?:[$€£]\s?\d|\b\d+(?:\.\d+)?\s?(?:billion|million|bn|mn)\b)", re.I)),
    ("country-count claim", re.compile(r"\b\d{2,}\s+countries\b", re.I)),
    ("named external partnership", re.compile(r"\b(partner(?:ship)?|collaboration|alliance)\s+(?:with|between)\s+[A-Z][A-Za-z0-9& .-]+", re.I)),
]

AI_TERMS = re.compile(r"\bAI\b|artificial intelligence|Human \+ AI|AI-enabled", re.I)
ACTION_TERMS = re.compile(r"\b(use|focus|prioriti[sz]e|build|enable|support|scale|sequence|translate|activate|mobilize|reinforce|develop|align)\b", re.I)
NUMERIC_ANCHOR = re.compile(r"(?:[+-]?\d+(?:\.\d+)?\s?(?:%|points?|ppts?|participants?)|above benchmark|below benchmark|in line with benchmark)", re.I)
EXECUTIVE_QUANT_ANCHOR = re.compile(r"[+-]?\d{1,3}(?:,\d{3})*(?:\.\d+)?\s*(?:%|percentage points?|points?|ppts?|participants?)", re.I)
PARTICIPANT_COUNT_ANCHOR = re.compile(r"\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\s+assessed\s+participants\b|\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\s+participants\b", re.I)
SIGNED_DIRECTION_CONTRADICTION = re.compile(
    r"(?:-\s*\d+(?:\.\d+)?\s*(?:percentage points?|points?|ppts?)\s+(?:above|over)|\+\s*\d+(?:\.\d+)?\s*(?:percentage points?|points?|ppts?)\s+(?:below|under))\s+(?:the\s+)?(?:benchmark)?",
    re.I,
)
HERO_SUBTITLE_BANNED = re.compile(
    r"\b(directional|readout|this report|this analysis|this summary|this view|the report|the analysis|the findings describe|the results describe)\b",
    re.I,
)


def _text(model: dict[str, Any], field: str, narrative: dict[str, Any] | None = None) -> str:
    values = narrative if narrative is not None else (model.get("narrative", {}) or {})
    return str(values.get(field, "") or "").strip()


def _sources_with_urls(model: dict[str, Any]) -> list[dict[str, Any]]:
    sources = model.get("external_context", {}).get("sources", []) or []
    return url_backed_sources(sources)


def _evidence_sources_with_urls(model: dict[str, Any]) -> list[dict[str, Any]]:
    return external_evidence_sources(model.get("external_context", {}) or {}, infer_title=False)


def _invalid_source_urls(model: dict[str, Any]) -> list[str]:
    context = model.get("external_context", {}) or {}
    sources = context.get("sources", []) or []
    invalid = []
    for src in normalized_external_sources(sources, infer_title=False):
        url = str(src.get("url") or "").strip()
        if url and not is_url_backed(url):
            invalid.append(url)
    for bullet in normalized_vetted_context_bullets(context.get("vetted_context_bullets") or []):
        url = str(bullet.get("source_url") or "").strip()
        if url and not is_url_backed(url):
            invalid.append(url)
    return invalid


def _vetted_bullet_issues(model: dict[str, Any]) -> list[str]:
    bullets = normalized_vetted_context_bullets((model.get("external_context", {}) or {}).get("vetted_context_bullets") or [])
    issues = []
    for idx, bullet in enumerate(bullets, start=1):
        prefix = f"external_context.vetted_context_bullets[{idx}]"
        if len(str(bullet.get("claim") or "").strip()) < 15:
            issues.append(f"{prefix} should include a concise factual claim")
        if not str(bullet.get("source_title") or "").strip():
            issues.append(f"{prefix} should include a source_title/title/name/label")
        url = str(bullet.get("source_url") or "").strip()
        if not url:
            issues.append(f"{prefix} should include a source_url/url")
        elif not is_url_backed(url):
            issues.append(f"{prefix} contains an invalid source_url that is not http(s): {url}")
        if not str(bullet.get("use") or "").strip():
            issues.append(f"{prefix} should include a use/purpose/context note")
    return issues


def _all_narrative_text(model: dict[str, Any]) -> str:
    chunks = []
    values = model.get("narrative", {}) or {}
    chunks.extend(str(v) for v in values.values() if isinstance(v, str))
    for narrative in (model.get("benchmark_narratives", {}) or {}).values():
        if isinstance(narrative, dict):
            chunks.extend(str(v) for v in narrative.values() if isinstance(v, str))
            for item in narrative.get("follow_up_opportunities", []) or []:
                if isinstance(item, dict):
                    chunks.extend(str(v) for v in item.values() if isinstance(v, str))
    return "\n".join(chunks)


def validate_model_messages(model: dict[str, Any], strict: bool = True) -> list[str]:
    issues: list[str] = []
    narrative = model.get("narrative", {}) or {}

    if strict and model.get("narrative_status") != "final":
        issues.append("content_model.narrative_status must be 'final' before client-ready rendering")

    views = benchmark_views(model)
    benchmarks = model.get("benchmarks") or []
    for benchmark in benchmarks:
        bid = benchmark.get("id")
        if bid and bid not in views:
            issues.append(f"benchmark_views.{bid} is missing for configured benchmark {benchmark.get('label', bid)}")
    narrative_sets: list[tuple[str, dict[str, Any], dict[str, Any]]] = []
    if len(views) > 1:
        for bid in views.keys():
            view_model = model_for_benchmark(model, bid)
            narrative_sets.append((f"benchmark_narratives.{bid}", view_model, narrative_for_benchmark(model, bid)))
    else:
        narrative_sets.append(("narrative", model, narrative))

    for prefix, view_model, values in narrative_sets:
        for field in required_narrative_fields(view_model):
            value = str(values.get(field, "") or "").strip()
            if len(value) < 20:
                issues.append(f"{prefix}.{field} is missing or too short for final rendering")
            elif any(pattern.search(value) for pattern in PLACEHOLDER_PATTERNS):
                issues.append(f"{prefix}.{field} appears to contain placeholder/draft text")

    # Positive-content checks: enforce a minimum substance floor without forcing
    # every paragraph into the same formula.
    client = model.get("client", {}) or {}
    client_names = [str(client.get("short_name", "") or "").strip(), str(client.get("legal_name", "") or "").strip()]
    client_names = [name for name in client_names if name]
    hero = f"{_text(model, 'hero_h1')} {_text(model, 'hero_p')}"
    executive = f"{_text(model, 'executive_p1')} {_text(model, 'executive_p2')}"
    follow_up = "\n".join(
        str(part or "") for item in (narrative.get("follow_up_opportunities") or [])
        for part in ([item.get("title"), item.get("text")] if isinstance(item, dict) else item)
    ) if narrative.get("follow_up_opportunities") else ""

    if not AI_TERMS.search(hero):
        issues.append("hero narrative should include an AI/Human + AI implication")
    hero_subtitle = _text(model, "hero_p")
    if HERO_SUBTITLE_BANNED.search(hero_subtitle):
        issues.append("hero subheading should state the implication directly and must not use directional/report/readout description language")
    if not AI_TERMS.search(executive):
        issues.append("executive narrative should include an AI/Human + AI implication")
    if not NUMERIC_ANCHOR.search(executive):
        issues.append("executive narrative should include at least one concise data anchor or benchmark direction")
    executive_quant_anchors = EXECUTIVE_QUANT_ANCHOR.findall(executive)
    if len(executive_quant_anchors) > 1:
        issues.append("executive narrative contains too many quantitative anchors; use no more than one concise score/participant anchor and lead with insight")
    if PARTICIPANT_COUNT_ANCHOR.search(executive):
        issues.append("executive narrative should not use participant count as its data anchor; participant count belongs in About the Data")
    follow_up_items = narrative.get("follow_up_opportunities") or []
    if len(follow_up_items) != 4:
        issues.append("narrative.follow_up_opportunities should contain exactly four client-ready recommendations")
    if not ACTION_TERMS.search(executive + "\n" + follow_up):
        issues.append("executive/follow-up narrative should include action-oriented language")

    invalid_urls = _invalid_source_urls(model)
    for url in invalid_urls:
        issues.append(f"external_context.sources or vetted_context_bullets contains an invalid external source URL that is not http(s): {url}")
    issues.extend(_vetted_bullet_issues(model))
    sources = _sources_with_urls(model)
    evidence_sources = _evidence_sources_with_urls(model)
    ai_summary = str(model.get("external_context", {}).get("ai_strategy_summary", "") or "").strip()
    if ai_summary and not evidence_sources:
        issues.append("external_context.ai_strategy_summary is populated, but no URL-backed external_context.sources or vetted_context_bullets are provided")
    for src in sources:
        if not src.get("title"):
            issues.append("each external_context.sources item with a URL should include a title/name/label")
        if not src.get("purpose"):
            issues.append("each external_context.sources item with a URL should include a concise purpose/context note")

    narrative_text = _all_narrative_text(model)
    if SIGNED_DIRECTION_CONTRADICTION.search(narrative_text):
        issues.append("narrative contains a signed benchmark-direction contradiction, such as a negative gap described as above benchmark or a positive gap described as below benchmark")
    for label, pattern in HIGH_RISK_EXTERNAL_FACT_PATTERNS:
        if pattern.search(narrative_text) and not evidence_sources:
            issues.append(f"narrative contains a high-risk external fact pattern ({label}) but no URL-backed sources")

    # Ensure card labels and narrative framing do not overstate below-benchmark data.
    largest = model.get("metrics", {}).get("largest_advantage", {}) or {}
    largest_gap = float(largest.get("gap_vs_benchmark", 0) or 0)
    largest_label = str(model.get("metrics", {}).get("largest_advantage_label", "") or "")
    largest_text = _text(model, "largest_narrative")
    if largest_gap <= 0:
        if largest_label != "Relative Strength":
            issues.append("metrics.largest_advantage_label must be 'Relative Strength' when the top responsibility gap is <= 0")
        if re.search(r"\blargest advantage\b|\bclear advantage\b|\babove benchmark\b", largest_text, re.I):
            issues.append("largest_narrative must not overstate non-positive top gap as an above-benchmark advantage")

    watch = model.get("metrics", {}).get("watch_area", {}) or {}
    watch_gap = float(watch.get("gap_vs_benchmark", 0) or 0)
    watch_text = _text(model, "watch_narrative")
    if watch_gap > 0:
        lower_watch = watch_text.lower()
        negative_watch_language = bool(re.search(r"\bbelow benchmark\b|\bweakness\b|\blow readiness\b|\btrails?\b", watch_text, re.I))
        if "deficit" in lower_watch and "not as a deficit" not in lower_watch and "not a deficit" not in lower_watch:
            negative_watch_language = True
        if negative_watch_language:
            issues.append("watch_narrative should acknowledge that the watch area is still above benchmark when the lowest gap is positive")

    return issues


def validate_model_issues(model: dict[str, Any], strict: bool = True) -> list[dict[str, str]]:
    """Return machine-actionable validation issue records for AI operators."""
    return [issue_record(message) for message in validate_model_messages(model, strict=strict)]


def validate_model(model: dict[str, Any], strict: bool = True) -> list[str]:
    """Return backward-compatible formatted validation issues with stable issue codes."""
    return [format_issue(record) for record in validate_model_issues(model, strict=strict)]


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate finalized AIRL Pulse content_model.json before rendering.")
    parser.add_argument("content_model")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--allow-draft", action="store_true", help="Skip the narrative_status='final' requirement for development checks.")
    args = parser.parse_args()

    path = Path(args.content_model)
    if not path.exists():
        print(f"ERROR: content model not found: {path}")
        return 2
    model = json.loads(path.read_text(encoding="utf-8"))
    issues = validate_model(model, strict=not args.allow_draft)
    if args.json:
        print(json.dumps({"issue_count": len(issues), "issues": validate_model_issues(model, strict=not args.allow_draft)}, indent=2))
    elif issues:
        print(f"Content model validation found {len(issues)} issue(s).")
        for issue in issues:
            print(f"- {issue}")
    else:
        print("Content model validation passed: final narrative contract is satisfied.")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
