"""Shared deterministic constants for AIRL Pulse report scripts."""
from __future__ import annotations

AI_READY_RESPONSIBILITY_ORDER = [
    "Sustain the Vision",
    "Take Decisive Action",
    "Scale for Impact",
    "Don't Stop at Success",
    "Champion Learning and Unlearning",
    "Address Fears",
]

AI_READY_RESPONSIBILITY_DISPLAY = {
    "Sustain the Vision": "Sustain the Vision",
    "Take Decisive Action": "Take Decisive Action",
    "Scale for Impact": "Scale For Impact",
    "Don't Stop at Success": "Don't Stop at Success",
    "Champion Learning and Unlearning": "Champion Learning & Unlearning",
    "Address Fears": "Address Fears",
}

AI_READY_RESPONSIBILITY_DEFINITIONS = {
    "Sustain the Vision": "Anchor teams around a compelling AI-based vision, maintain focus, and remain committed.",
    "Take Decisive Action": "Act with deliberate urgency. Balance the need to perfect, progress, pause and stop.",
    "Scale for Impact": "Prioritize efforts that maximize scale and impact over fragmented experiments.",
    "Don't Stop at Success": "Avoid complacency and foster a culture of continuous iteration and alternative thinking.",
    "Champion Learning and Unlearning": "Spark a mindset of rapid learning and unlearning, and encourage a rethink of long-held habits.",
    "Address Fears": "Address fears around AI's impact on jobs with integrity and authenticity.",
}

_RESPONSIBILITY_ALIASES = {
    "Scale For Impact": "Scale for Impact",
    "Champion Learning & Unlearning": "Champion Learning and Unlearning",
    "Don’t Stop at Success": "Don't Stop at Success",
}


def normalize_responsibility_name(value: object) -> str:
    """Return the canonical internal responsibility name used by all scripts."""
    text = "" if value is None else str(value).strip()
    return _RESPONSIBILITY_ALIASES.get(text, text)


def responsibility_label_variants() -> list[str]:
    """Return canonical, display, and accepted alias labels for narrative linting."""
    labels = set(AI_READY_RESPONSIBILITY_ORDER)
    labels.update(AI_READY_RESPONSIBILITY_DISPLAY.values())
    labels.update(_RESPONSIBILITY_ALIASES.keys())
    return sorted(labels)
