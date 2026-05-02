"""Unit tests for the notes tool using a temp file path."""

from pathlib import Path

import pytest

from src.tools.notes import notes_add, notes_list


@pytest.fixture
def temp_notes(tmp_path: Path) -> Path:
    return tmp_path / "notes.json"


def test_add_then_list(temp_notes):
    r1 = notes_add("first note", _path=temp_notes)
    assert r1["ok"] is True
    assert r1["note"]["id"] == 1
    assert r1["count"] == 1

    r2 = notes_add("second note", _path=temp_notes)
    assert r2["note"]["id"] == 2
    assert r2["count"] == 2

    listed = notes_list(_path=temp_notes)
    assert listed["count"] == 2
    assert [n["text"] for n in listed["notes"]] == ["first note", "second note"]


def test_list_on_missing_file_is_empty(temp_notes):
    assert not temp_notes.exists()
    r = notes_list(_path=temp_notes)
    assert r == {"ok": True, "count": 0, "notes": []}


def test_add_rejects_empty_text(temp_notes):
    r = notes_add("   ", _path=temp_notes)
    assert r["ok"] is False
    assert "non-empty" in r["error"]


def test_add_strips_whitespace(temp_notes):
    r = notes_add("  hello  ", _path=temp_notes)
    assert r["note"]["text"] == "hello"


def test_corrupt_file_is_treated_as_empty(temp_notes):
    temp_notes.write_text("this is not json", encoding="utf-8")
    listed = notes_list(_path=temp_notes)
    assert listed["count"] == 0
    # And writing on top should still work
    r = notes_add("recovers", _path=temp_notes)
    assert r["ok"] is True
