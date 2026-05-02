"""Local-file notes tool.

Notes are stored as a JSON list at data/notes.json. The file is created on
first write. Each note has an integer id, an ISO timestamp, and the text.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from config import NOTES_FILE


def _load(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _save(path: Path, notes: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(notes, f, indent=2, ensure_ascii=False)


def notes_add(text: str, _path: Path | None = None) -> Dict[str, Any]:
    """Append a note. `_path` is overridable for tests."""
    if not isinstance(text, str) or not text.strip():
        return {"ok": False, "error": "text must be a non-empty string"}
    path = _path or NOTES_FILE
    notes = _load(path)
    new_id = (max((n.get("id", 0) for n in notes), default=0) + 1)
    entry = {
        "id": new_id,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "text": text.strip(),
    }
    notes.append(entry)
    _save(path, notes)
    return {"ok": True, "note": entry, "count": len(notes)}


def notes_list(_path: Path | None = None) -> Dict[str, Any]:
    """Return all saved notes."""
    path = _path or NOTES_FILE
    notes = _load(path)
    return {"ok": True, "count": len(notes), "notes": notes}
