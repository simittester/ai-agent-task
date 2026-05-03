"""Wikipedia tool tests. We mock the `wikipedia` module to avoid network."""

from types import SimpleNamespace
from unittest.mock import patch

import src.tools.wikipedia_lookup as wikimod


def test_happy_path(monkeypatch):
    fake_page = SimpleNamespace(title="Alan Turing", url="https://en.wikipedia.org/wiki/Alan_Turing")
    monkeypatch.setattr(wikimod.wikipedia, "summary", lambda *a, **k: "Alan Turing was a British mathematician.")
    monkeypatch.setattr(wikimod.wikipedia, "page", lambda *a, **k: fake_page)

    r = wikimod.wikipedia_lookup("Alan Turing")
    assert r["ok"] is True
    assert r["title"] == "Alan Turing"
    assert "mathematician" in r["summary"]


def test_empty_query_rejected():
    r = wikimod.wikipedia_lookup("   ")
    assert r["ok"] is False


def test_missing_page_returns_error(monkeypatch):
    def raise_page_error(*a, **k):
        raise wikimod.wikipedia.PageError("zzzzz")
    monkeypatch.setattr(wikimod.wikipedia, "summary", raise_page_error)
    r = wikimod.wikipedia_lookup("nonexistent-topic-zzz")
    assert r["ok"] is False
    assert "no Wikipedia page" in r["error"]


def test_disambiguation_falls_back_to_first_option(monkeypatch):
    call_count = {"summary": 0}
    fake_page = SimpleNamespace(title="Mercury (element)", url="https://en.wikipedia.org/wiki/Mercury_(element)")

    def summary(query, *a, **k):
        call_count["summary"] += 1
        if call_count["summary"] == 1:
            raise wikimod.wikipedia.DisambiguationError("Mercury", ["Mercury (element)", "Mercury (planet)"])
        return "A chemical element with the symbol Hg."

    monkeypatch.setattr(wikimod.wikipedia, "summary", summary)
    monkeypatch.setattr(wikimod.wikipedia, "page", lambda *a, **k: fake_page)

    r = wikimod.wikipedia_lookup("Mercury")
    assert r["ok"] is True
    assert "Hg" in r["summary"]
    assert "disambiguation" in r["note"]
