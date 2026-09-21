#!/usr/bin/env python3
"""Lint AIRL Pulse narrative fields for label-led prose and minimum content quality.

This linter is intentionally conservative and should be run after ChatGPT has
refined the `narrative` portion of the content model and before HTML rendering.
It scans narrative-like text only. It does not lint table labels, chart labels,
card titles, section headings, legends, tooltips, or raw data fields.

Exit code:
  0 = no blocking issues found
  1 = blocking narrative issues were found and should be rewritten before rendering
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

from airl_constants import responsibility_label_variants


LINT_ISSUE_CATALOG = {
    "STYLE_HERO_IMPLICATION": {
        "category": "narrative_style",
        "action": "Rewrite narrative.hero_p as a direct AI/Human + AI leadership implication, not report methodology or sample-description language.",
    },
    "STYLE_PROCESS_REFERENCE": {
        "category": "narrative_style",
        "action": "Remove references to drafts, revisions, refreshed reports, prior versions, or production process from client-facing prose.",
    },
    "STYLE_BENCHMARK_FRAMING": {
        "category": "narrative_style",
        "action": "Rewrite the High Engagement narrative so the leadership finding leads. Remove legacy stretch/higher-bar/aspiration framing and use the benchmark name only when a specific comparison needs orientation.",
    },
    "STYLE_LABEL_LED": {
        "category": "narrative_style",
        "action": "Rewrite the flagged field so it translates labels into behavioral meaning and implication instead of listing visible labels.",
    },
    "STYLE_LOW_TARGET_CONSTRUCT": {
        "category": "narrative_style",
        "action": "Rewrite Structure/Balance interpretation using their low-target profile meaning. Stronger profile fit means lower need for the named construct, not more of it.",
    },
    "VALIDATION_GENERAL": {
        "category": "content_contract",
        "action": "Fix the flagged model or narrative issue, then rerun lint before rendering.",
    },
}


def lint_meta(code: str) -> dict[str, str]:
    return LINT_ISSUE_CATALOG.get(code, LINT_ISSUE_CATALOG["VALIDATION_GENERAL"])


def make_lint_issue(path: str, reasons: list[str], text_preview: str = "", labels: list[str] | None = None, code: str = "STYLE_LABEL_LED") -> dict[str, Any]:
    meta = lint_meta(code)
    return {
        "code": code,
        "category": meta["category"],
        "action": meta["action"],
        "path": path,
        "labels": labels or [],
        "reasons": sorted(set(reasons)),
        "text_preview": text_preview,
    }

RESPONSIBILITY_LABELS = responsibility_label_variants()

PROBLEM_PHRASES = [
    "the strongest responsibility is",
    "the strongest responsibilities are",
    "the watchpoints are",
    "the top differentiators are",
    "the strongest signals are",
    "the signal is strongest in",
    "the highest differentiators are",
    "the relative watchpoints are",
]




EXECUTIVE_CONTEXT_META_PATTERNS = [
    ("public strategy context meta-reference", re.compile(r"\b(public|external|web|strategy)\s+context\b", re.I)),
    ("against context construction", re.compile(r"\bAgainst\s+(the\s+)?(public|external|web|strategy)?\s*context\b", re.I)),
    ("vague context raises the bar", re.compile(r"\bcontext\s+raises\s+the\s+bar\b", re.I)),
]

PUNCTUATION_PROBLEM_PATTERNS = [
    ("period-comma punctuation", re.compile(r"\.,")),
    ("comma-period punctuation", re.compile(r",\.")),
]

REPORT_SELF_REFERENCE_PATTERNS = [
    ("updated report", re.compile(r"\b(this|the)\s+updated\s+report\b|\bupdated\s+analysis\b", re.I)),
    ("fresh read", re.compile(r"\bfresh\s+(read|look|view|analysis)\b", re.I)),
    ("refreshed report", re.compile(r"\b(this|the)\s+refresh(ed)?\b|\brefreshed\s+(report|analysis|view|read)\b", re.I)),
    ("regenerated report", re.compile(r"\b(re-?generated|newly\s+generated|recreated)\s+(report|analysis|view)\b", re.I)),
    ("new version", re.compile(r"\b(this|the)\s+new\s+version\b|\bprior\s+version\b|\bprevious\s+version\b", re.I)),
    ("production-process reference", re.compile(r"\b(as\s+requested|in\s+this\s+revision|for\s+this\s+iteration|this\s+draft)\b", re.I)),
]


BENCHMARK_REFERENTIAL_PATTERNS = [
    ("legacy stretch benchmark framing", re.compile(r"\bstretch\s+(benchmark|comparison|standard|view|target|opportunity)\b", re.I)),
    ("higher-bar benchmark framing", re.compile(r"\b(higher\s+(bar|aspiration|standard)|under\s+a\s+higher\s+bar)\b", re.I)),
    ("aspiration-gap framing", re.compile(r"\baspiration\s+gap\b", re.I)),
    ("benchmark-as-subject framing", re.compile(r"\b(?:the\s+)?(?:high\s+engagement\s+)?benchmark\s+(shifts?|raises?|changes?|reframes?)\b", re.I)),
]


LOW_TARGET_CONSTRUCT_PATTERNS = [
    ("Structure direction reversed", re.compile(r"\b(?:high(?:er)?|more|greater|strong(?:er)?|enough)\s+Structure\b", re.I)),
    ("Balance direction reversed", re.compile(r"\b(?:high(?:er)?|more|greater|strong(?:er)?)\s+Balance\b", re.I)),
]

HERO_SUBTITLE_PROBLEM_PATTERNS = [
    ("participant/sample count", re.compile(r"\b\d{2,}\b.*\b(assessed\s+)?(leaders|participants|contributors|respondents)\b", re.I)),
    ("assessed participants phrase", re.compile(r"\bassessed\s+(leaders|participants|contributors|respondents)\b", re.I)),
    ("sample/report description", re.compile(r"\b(results?|data|assessment|findings|report|readout|summary|analysis|view)\s+(describe|describes|show|shows|indicate|indicates|provide|provides|highlight|highlights|draws on|reflect|reflects)\b", re.I)),
    ("this-readout lead-in", re.compile(r"\bthis\s+(directional\s+)?(readout|report|analysis|summary|view)\s+(reflects|shows|indicates|points|suggests|highlights|draws on)\b", re.I)),
    ("sample records lead-in", re.compile(r"\b(sample|directional\s+readout)\s+across\b.*\brecords\b", re.I)),
    ("readiness profile across", re.compile(r"\breadiness\s+profile\s+across\b", re.I)),
    ("directional sample lead-in", re.compile(r"\b(early-read\s+signal\s+draws\s+on|directional\s+readout)\b", re.I)),
    ("methodology language", re.compile(r"\bshould\s+be\s+read\s+directionally\b|\bdirectional\s+readiness\s+profile\b", re.I)),
    ("directional hero language", re.compile(r"\bdirectional\b", re.I)),
]

NARRATIVE_KEY_HINTS = {
    "narrative", "paragraph", "body", "text", "lede", "summary", "insight",
    "implication", "recommendation", "callout", "story", "storyline",
    "opportunity", "rationale", "description", "takeaway", "content",
}

NON_NARRATIVE_KEY_HINTS = {
    "title", "heading", "header", "label", "name", "display", "legend",
    "tooltip", "axis", "row", "column", "table", "chart", "source",
    "url", "definition", "responsibility", "construct", "composite", "metric",
    "count", "pct", "score", "gap", "n", "id", "code", "date", "year",
}


def load_extra_labels(skill_root: Path) -> list[str]:
    """Load construct/composite labels from the bundled reference markdown."""
    labels: set[str] = set(RESPONSIBILITY_LABELS)
    ref = skill_root / "references" / "construct_composite_definitions.md"
    if not ref.exists():
        return sorted(labels, key=len, reverse=True)

    text = ref.read_text(encoding="utf-8", errors="ignore")

    # Responsibility headings.
    for match in re.finditer(r"^##\s+(.+?)\s*$", text, flags=re.M):
        value = match.group(1).strip()
        if value and value.lower() not in {"how to use this reference", "responsibility map"}:
            labels.add(value)

    # Markdown table construct column: | CODE | Construct | ... |
    for line in text.splitlines():
        if not line.startswith("|") or "---" in line:
            continue
        parts = [p.strip() for p in line.strip("|").split("|")]
        if len(parts) >= 2 and parts[0] and parts[1]:
            first, second = parts[0], parts[1]
            if first.lower() not in {"code", ""} and second.lower() not in {"construct", ""}:
                # Ignore obvious definitions and long fragments.
                if 2 <= len(second) <= 60:
                    labels.add(second)

    # Add common ampersand/and variants.
    expanded = set(labels)
    for label in labels:
        if " and " in label:
            expanded.add(label.replace(" and ", " & "))
        if " & " in label:
            expanded.add(label.replace(" & ", " and "))
    return sorted(expanded, key=len, reverse=True)


def compile_label_patterns(labels: Iterable[str]) -> list[tuple[str, re.Pattern[str]]]:
    patterns = []
    for label in labels:
        # Avoid single-letter or code-like labels. Exact phrase matching with
        # loose whitespace protects terms like "Challenge" while avoiding
        # partial matches inside longer words.
        if len(label.strip()) < 4:
            continue
        escaped = re.escape(label).replace(r"\ ", r"\s+")
        pattern = re.compile(rf"(?<![A-Za-z0-9]){escaped}(?![A-Za-z0-9])", re.I)
        patterns.append((label, pattern))
    return patterns


def find_labels(text: str, patterns: list[tuple[str, re.Pattern[str]]]) -> list[str]:
    found: list[str] = []
    for label, pattern in patterns:
        if pattern.search(text):
            # De-duplicate variants that point to effectively the same label.
            canonical = label.replace("&", "and").replace("Don’t", "Don't").lower()
            if canonical not in [f.replace("&", "and").replace("Don’t", "Don't").lower() for f in found]:
                found.append(label)
    return found


def key_has_any(key: str, hints: set[str]) -> bool:
    k = key.lower()
    tokens = {t for t in re.split(r"[^a-z0-9]+", k) if t}
    for h in hints:
        if len(h) <= 2:
            if h in tokens:
                return True
        elif h in k:
            return True
    return False


def is_narrative_string(path: tuple[str, ...], value: str) -> bool:
    if not value or len(value.strip()) < 35:
        return False
    last = path[-1] if path else ""
    full = ".".join(path).lower()

    # The narrative object is designed to contain prose fields. Still skip
    # title-like keys inside it.
    if path and path[0] == "narrative":
        return not key_has_any(last, NON_NARRATIVE_KEY_HINTS)

    if key_has_any(last, NON_NARRATIVE_KEY_HINTS):
        return False
    if key_has_any(last, NARRATIVE_KEY_HINTS) or any(f".{h}" in full for h in NARRATIVE_KEY_HINTS):
        return True
    return False


def walk_strings(obj: Any, path: tuple[str, ...] = ()):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk_strings(v, path + (str(k),))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_strings(v, path + (f"[{i}]",))
    elif isinstance(obj, str):
        yield path, obj


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]



def lint_hero_subtitle(model: dict[str, Any]) -> list[dict[str, Any]]:
    """Flag generic/sample-description hero subtitles before rendering."""
    text = str(model.get("narrative", {}).get("hero_p", "") or "").strip()
    if not text:
        return []
    reasons: list[str] = []
    for reason, pattern in HERO_SUBTITLE_PROBLEM_PATTERNS:
        if pattern.search(text):
            reasons.append(reason)

    # The hero subtitle should be an implication, not a methodology caveat.
    lower = text.lower()
    if lower.startswith((
        "the results describe", "the data shows", "the assessment indicates",
        "this report highlights", "this report reflects", "this report shows",
        "this readout", "this directional readout", "this analysis",
        "the findings suggest", "the results provide",
        "this early-read signal draws on", "across ",
    )):
        reasons.append("generic report/sample-description lead-in")

    if reasons:
        return [make_lint_issue(
            "narrative.hero_p",
            reasons,
            re.sub(r"\s+", " ", text)[:260],
            code="STYLE_HERO_IMPLICATION",
        )]
    return []

def lint_model(model: dict[str, Any], labels: list[str]) -> list[dict[str, Any]]:
    patterns = compile_label_patterns(labels)
    issues: list[dict[str, Any]] = []

    largest = str(model.get("metrics", {}).get("largest_advantage", {}).get("display", "") or "")
    watch = str(model.get("metrics", {}).get("watch_area", {}).get("display", "") or "")
    title_sensitive = {
        "largest_narrative": largest,
        "watch_narrative": watch,
    }

    for path, text in walk_strings(model):
        if not is_narrative_string(path, text):
            continue
        path_str = ".".join(path)
        found = find_labels(text, patterns)
        if not found:
            continue

        lower = text.lower()
        reasons: list[str] = []

        # Label lists or serial phrases in a paragraph.
        if len(found) >= 3:
            reasons.append("contains three or more labels in narrative prose")

        for sentence in split_sentences(text):
            sfound = find_labels(sentence, patterns)
            if len(sfound) >= 2 and ("," in sentence or " and " in sentence.lower() or " & " in sentence):
                reasons.append("contains a serial/comma-separated label list")
                break

        if any(phrase in lower for phrase in PROBLEM_PHRASES):
            reasons.append("uses a prohibited label-led phrase")

        # Card-body repetition of visible title labels.
        last = path[-1] if path else ""
        for key, visible_label in title_sensitive.items():
            if key in last and visible_label:
                if find_labels(". ".join(split_sentences(text)[:1]), compile_label_patterns([visible_label])):
                    reasons.append(f"opening sentence repeats visible card-title label: {visible_label}")
                elif find_labels(text, compile_label_patterns([visible_label])):
                    reasons.append(f"repeats visible card-title label: {visible_label}")

        # Executive narrative should not list responsibility names.
        if path_str.startswith("narrative.executive"):
            resp_found = find_labels(text, compile_label_patterns(RESPONSIBILITY_LABELS))
            if len(resp_found) >= 2:
                reasons.append("executive narrative contains multiple responsibility labels")

        if reasons:
            issues.append(make_lint_issue(
                path_str,
                reasons,
                re.sub(r"\s+", " ", text.strip())[:260],
                labels=found,
                code="STYLE_LABEL_LED",
            ))

    return issues



def lint_low_target_construct_direction(model: dict[str, Any]) -> list[dict[str, Any]]:
    """Block literal interpretations that reverse low-target Structure/Balance meaning."""
    issues: list[dict[str, Any]] = []
    for path, text in walk_strings(model):
        if not is_narrative_string(path, text):
            continue
        reasons = [reason for reason, pattern in LOW_TARGET_CONSTRUCT_PATTERNS if pattern.search(text)]
        if reasons:
            issues.append(make_lint_issue(
                ".".join(path),
                reasons,
                re.sub(r"\s+", " ", text.strip())[:260],
                code="STYLE_LOW_TARGET_CONSTRUCT",
            ))
    return issues

def lint_benchmark_referential_framing(model: dict[str, Any]) -> list[dict[str, Any]]:
    """Flag legacy comparative framing in High Engagement benchmark narrative."""
    issues: list[dict[str, Any]] = []
    high = (model.get("benchmark_narratives") or {}).get("high_engagement") or {}
    for path, text in walk_strings(high, ("benchmark_narratives", "high_engagement")):
        if not isinstance(text, str) or len(text.strip()) < 20:
            continue
        reasons = [reason for reason, pattern in BENCHMARK_REFERENTIAL_PATTERNS if pattern.search(text)]
        if reasons:
            issues.append(make_lint_issue(
                ".".join(path),
                reasons,
                re.sub(r"\s+", " ", text.strip())[:260],
                code="STYLE_BENCHMARK_FRAMING",
            ))
    return issues


def lint_report_self_reference(model: dict[str, Any]) -> list[dict[str, Any]]:
    """Flag report prose that references refreshes, prior versions, or generation process."""
    issues: list[dict[str, Any]] = []
    for path, text in walk_strings(model):
        if not is_narrative_string(path, text):
            continue
        reasons = [reason for reason, pattern in REPORT_SELF_REFERENCE_PATTERNS if pattern.search(text)]
        reasons.extend(reason for reason, pattern in PUNCTUATION_PROBLEM_PATTERNS if pattern.search(text))
        if ".".join(path).startswith("narrative.executive"):
            reasons.extend(reason for reason, pattern in EXECUTIVE_CONTEXT_META_PATTERNS if pattern.search(text))
        if reasons:
            issues.append(make_lint_issue(
                ".".join(path),
                reasons,
                re.sub(r"\s+", " ", text.strip())[:260],
                code="STYLE_PROCESS_REFERENCE",
            ))
    return issues


def lint_positive_content_contract(model: dict[str, Any]) -> list[dict[str, Any]]:
    """Run the positive content-model checks without requiring final status."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from validate_content_model import validate_model_issues
        messages = validate_model_issues(model, strict=False)
    except Exception as exc:
        return [make_lint_issue(
            "content_model",
            ["positive content validation could not run"],
            str(exc)[:260],
            code="VALIDATION_GENERAL",
        )]
    return [{
        "code": issue.get("code", "VALIDATION_GENERAL"),
        "category": issue.get("category", "content_contract"),
        "action": issue.get("action", lint_meta("VALIDATION_GENERAL")["action"]),
        "path": "content_model",
        "labels": [],
        "reasons": [issue.get("message", "content-model validation issue")],
        "text_preview": "",
    } for issue in messages]


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint AIRL Pulse narrative prose for label-led writing.")
    parser.add_argument("content_model", help="Path to content_model.json after narrative fields are drafted")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output")
    parser.add_argument("--skill-root", default=None, help="Skill root directory; defaults to parent of this script")
    args = parser.parse_args()

    path = Path(args.content_model)
    model = json.loads(path.read_text(encoding="utf-8"))
    skill_root = Path(args.skill_root) if args.skill_root else Path(__file__).resolve().parents[1]
    labels = load_extra_labels(skill_root)
    issues = lint_hero_subtitle(model) + lint_report_self_reference(model) + lint_benchmark_referential_framing(model) + lint_low_target_construct_direction(model) + lint_model(model, labels) + lint_positive_content_contract(model)

    if args.json:
        print(json.dumps({"issue_count": len(issues), "issues": issues}, indent=2))
    else:
        if not issues:
            print("Narrative lint passed: no blocking label-led or content-quality issues found.")
        else:
            print(f"Narrative lint found {len(issues)} issue(s). Rewrite flagged fields before rendering.\n")
            for i, issue in enumerate(issues, 1):
                print(f"{i}. [{issue.get('code', 'VALIDATION_GENERAL')}] {issue['path']}")
                print(f"   Category: {issue.get('category', 'content_contract')}")
                print(f"   Reasons: {', '.join(issue['reasons'])}")
                print(f"   Action: {issue.get('action', '')}")
                print(f"   Labels: {', '.join(issue['labels'])}")
                print(f"   Text: {issue['text_preview']}\n")

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
