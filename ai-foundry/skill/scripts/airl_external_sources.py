"""Shared external-source normalization helpers for AIRL report scripts."""
from __future__ import annotations

from urllib.parse import urlparse
from typing import Any


def source_label_from_url(url: object) -> str:
    """Return a compact display label for a URL when no source title is supplied."""
    raw = str(url or "").strip()
    try:
        host = urlparse(raw).netloc or raw
    except Exception:
        host = raw
    host = host.replace("www.", "")
    return host or "source"


def is_url_backed(url: object) -> bool:
    """Return True only for external http(s) URLs that can ground web context."""
    raw = str(url or "").strip()
    parsed = urlparse(raw)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def normalize_external_source(item: Any, infer_title: bool = True) -> dict[str, str]:
    """Normalize content_model.external_context.sources metadata.

    Supported item forms:
    - {"title": "Annual report", "url": "https://...", "purpose": "headcount"}
    - {"name": "Company AI page", "href": "https://..."}
    - "https://..." or "Company annual report"
    Raw URLs are used as link targets; the renderer should not display raw URLs
    as prose.
    """
    if isinstance(item, dict):
        url = str(item.get("url") or item.get("href") or item.get("link") or "").strip()
        title = str(item.get("title") or item.get("name") or item.get("label") or item.get("source") or "").strip()
        purpose = str(item.get("purpose") or item.get("use") or item.get("context") or "").strip()
        if infer_title and not title and url:
            title = source_label_from_url(url)
        return {"title": title, "url": url, "purpose": purpose}
    raw = str(item or "").strip()
    if not raw:
        return {"title": "", "url": "", "purpose": ""}
    if raw.startswith("http://") or raw.startswith("https://"):
        return {"title": source_label_from_url(raw), "url": raw, "purpose": ""}
    return {"title": raw, "url": "", "purpose": ""}


def normalized_external_sources(sources: Any, infer_title: bool = True) -> list[dict[str, str]]:
    """Return normalized external-source dictionaries from a source list."""
    return [normalize_external_source(item, infer_title=infer_title) for item in (sources or [])]


def url_backed_sources(sources: Any) -> list[dict[str, str]]:
    """Return normalized sources with valid http(s) URLs."""
    return [src for src in normalized_external_sources(sources, infer_title=False) if is_url_backed(src.get("url"))]


def normalize_vetted_context_bullet(item: Any) -> dict[str, str]:
    """Normalize optional external_context.vetted_context_bullets entries.

    Vetted bullets are an evidence ledger for AI operators. They ground
    company-specific external facts without constraining narrative synthesis.
    Supported keys intentionally allow common synonyms so older content models
    can be repaired without brittle reshaping.
    """
    if not isinstance(item, dict):
        raw = str(item or "").strip()
        return {"claim": raw, "source_title": "", "source_url": "", "use": ""}
    claim = str(item.get("claim") or item.get("fact") or item.get("bullet") or item.get("text") or "").strip()
    source_url = str(item.get("source_url") or item.get("url") or item.get("href") or item.get("link") or "").strip()
    source_title = str(
        item.get("source_title") or item.get("title") or item.get("source") or item.get("name") or item.get("label") or ""
    ).strip()
    use = str(item.get("use") or item.get("purpose") or item.get("context") or "").strip()
    return {"claim": claim, "source_title": source_title, "source_url": source_url, "use": use}


def normalized_vetted_context_bullets(bullets: Any) -> list[dict[str, str]]:
    """Return normalized optional external-context evidence bullets."""
    return [normalize_vetted_context_bullet(item) for item in (bullets or [])]


def evidence_source_from_bullet(bullet: dict[str, str]) -> dict[str, str]:
    """Return a source-entry shape derived from a vetted evidence bullet."""
    return {
        "title": bullet.get("source_title", ""),
        "url": bullet.get("source_url", ""),
        "purpose": bullet.get("use", ""),
    }


def external_evidence_sources(external_context: Any, infer_title: bool = False) -> list[dict[str, str]]:
    """Return URL-backed evidence sources from sources plus vetted bullets.

    This is intentionally broader than external_context.sources: a valid vetted
    bullet can ground a company-specific external claim even when the operator
    has not duplicated the same source in the display-oriented sources list.
    """
    context = external_context if isinstance(external_context, dict) else {}
    entries = list(context.get("sources") or [])
    for bullet in normalized_vetted_context_bullets(context.get("vetted_context_bullets") or []):
        entries.append(evidence_source_from_bullet(bullet))
    return [src for src in normalized_external_sources(entries, infer_title=infer_title) if is_url_backed(src.get("url"))]
