"""Web search tool tests. We mock DDGS to avoid network."""

import sys
import types

import src.tools.web_search as ws


class _FakeDDGS:
    def __init__(self, results):
        self._results = results
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def text(self, query, max_results=5):
        return self._results[:max_results]


def _install_fake(monkeypatch, results):
    fake_module = types.ModuleType("duckduckgo_search")
    fake_module.DDGS = lambda: _FakeDDGS(results)
    monkeypatch.setitem(sys.modules, "duckduckgo_search", fake_module)


def test_happy_path(monkeypatch):
    _install_fake(monkeypatch, [
        {"title": "Python", "href": "https://python.org", "body": "Python is a language."},
        {"title": "PEP 8", "href": "https://peps.python.org/pep-0008/", "body": "Style guide."},
    ])
    r = ws.web_search("python", max_results=2)
    assert r["ok"] is True
    assert r["count"] == 2
    assert r["results"][0]["url"] == "https://python.org"


def test_empty_query_rejected():
    r = ws.web_search("")
    assert r["ok"] is False


def test_max_results_clamped(monkeypatch):
    _install_fake(monkeypatch, [{"title": f"t{i}", "href": "u", "body": "b"} for i in range(20)])
    r = ws.web_search("x", max_results=999)
    assert r["count"] == 10  # clamped to 10


def test_network_error_is_wrapped(monkeypatch):
    class BoomDDGS:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def text(self, *a, **k): raise RuntimeError("network down")

    fake_module = types.ModuleType("duckduckgo_search")
    fake_module.DDGS = lambda: BoomDDGS()
    monkeypatch.setitem(sys.modules, "duckduckgo_search", fake_module)

    r = ws.web_search("anything")
    assert r["ok"] is False
    assert "network down" in r["error"]
