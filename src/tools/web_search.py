"""Web search via DuckDuckGo (no API key required)."""

from __future__ import annotations

from typing import Any, Dict


def web_search(query: str, max_results: int = 5) -> Dict[str, Any]:
    """Return a list of {title, url, snippet} dicts for the query."""
    if not isinstance(query, str) or not query.strip():
        return {"ok": False, "error": "query must be a non-empty string"}
    max_results = max(1, min(int(max_results), 10))

    try:
        # Imported lazily so tests that mock this module don't pay the import cost.
        # `ddgs` is the renamed successor to `duckduckgo_search`; same API.
        from ddgs import DDGS
    except ImportError as exc:
        return {"ok": False, "error": f"ddgs not installed: {exc}"}

    try:
        with DDGS() as ddgs:
            raw = list(ddgs.text(query, max_results=max_results))
    except Exception as exc:  # noqa: BLE001 — network / rate-limit / parse errors
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    results = [
        {
            "title": r.get("title", ""),
            "url": r.get("href", ""),
            "snippet": r.get("body", ""),
        }
        for r in raw
    ]
    return {"ok": True, "query": query, "count": len(results), "results": results}
