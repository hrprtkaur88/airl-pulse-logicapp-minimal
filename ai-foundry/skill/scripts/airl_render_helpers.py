#!/usr/bin/env python3
"""Shared rendering helpers for AIRL HTML report generation.

Keep this module limited to deterministic, side-effect-free formatting and
escaping helpers. Higher-level report assembly remains in render_report.py.
"""

import html


def esc(x):
    return html.escape(str(x), quote=True)


def safe_narratives(values):
    """Escape LLM-authored narrative strings before inserting into HTML."""
    return {key: esc(value) if isinstance(value, str) else value for key, value in values.items()}


def pct(x):
    return f"{round(float(x))}%"


def gap(x):
    return f"{float(x):+.1f}"


def gap0(x):
    r = round(float(x))
    return "0" if r == 0 else f"{r:+.0f}"
