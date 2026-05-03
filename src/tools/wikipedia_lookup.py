"""Wikipedia summary lookup tool."""

from __future__ import annotations

from typing import Any, Dict

import wikipedia


def wikipedia_lookup(query: str, sentences: int = 3) -> Dict[str, Any]:
    """Return a short Wikipedia summary for `query`.

    On disambiguation, picks the first option and reports it. On a missing
    page, returns an error result rather than raising.
    """
    if not isinstance(query, str) or not query.strip():
        return {"ok": False, "error": "query must be a non-empty string"}
    sentences = max(1, min(int(sentences), 10))
    try:
        summary = wikipedia.summary(query, sentences=sentences, auto_suggest=True, redirect=True)
        page = wikipedia.page(query, auto_suggest=True, redirect=True)
        return {
            "ok": True,
            "query": query,
            "title": page.title,
            "url": page.url,
            "summary": summary,
        }
    except wikipedia.DisambiguationError as exc:
        first = exc.options[0] if exc.options else None
        if first is None:
            return {"ok": False, "error": "disambiguation with no options"}
        try:
            summary = wikipedia.summary(first, sentences=sentences)
            page = wikipedia.page(first)
            return {
                "ok": True,
                "query": query,
                "title": page.title,
                "url": page.url,
                "summary": summary,
                "note": f"disambiguation; picked '{first}'",
            }
        except Exception as exc2:  # noqa: BLE001 — last-resort wrap for the tool boundary
            return {"ok": False, "error": f"disambiguation fallback failed: {exc2}"}
    except wikipedia.PageError:
        return {"ok": False, "error": f"no Wikipedia page found for '{query}'"}
    except Exception as exc:  # noqa: BLE001 — network etc.
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
