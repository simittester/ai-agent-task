"""Tool registry.

Each tool is a callable plus a JSON-serialisable schema describing its
arguments. The agent passes the schemas to the LLM; the LLM responds with a
tool name + arguments; the agent looks the tool up here and calls it.
"""

from __future__ import annotations

from typing import Any, Callable, Dict

# Aliased to avoid shadowing the submodule attributes (web_search.py etc.)
# on the package namespace, which would break `import src.tools.web_search`.
from src.tools.calculator import calculator as _calculator
from src.tools.notes import notes_add as _notes_add, notes_list as _notes_list
from src.tools.web_search import web_search as _web_search
from src.tools.wikipedia_lookup import wikipedia_lookup as _wikipedia_lookup


ToolFunc = Callable[..., Dict[str, Any]]


TOOLS: Dict[str, ToolFunc] = {
    "calculator": _calculator,
    "notes_add": _notes_add,
    "notes_list": _notes_list,
    "web_search": _web_search,
    "wikipedia_lookup": _wikipedia_lookup,
}


# Gemini function-declaration schemas. Kept close to the registry so adding a
# tool means touching one file.
TOOL_SCHEMAS = [
    {
        "name": "calculator",
        "description": (
            "Evaluate a single arithmetic expression and return its numeric "
            "result. Supports +, -, *, /, **, parentheses, and the functions "
            "sqrt, sin, cos, tan, log, exp. Use this whenever a question "
            "requires exact arithmetic."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Arithmetic expression, e.g. '2 * (3 + 4)' or 'sqrt(2)'.",
                },
            },
            "required": ["expression"],
        },
    },
    {
        "name": "wikipedia_lookup",
        "description": (
            "Fetch a short summary of a topic from English Wikipedia. Best "
            "for well-known concepts, people, places, and events."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Topic to look up, e.g. 'Alan Turing'.",
                },
                "sentences": {
                    "type": "integer",
                    "description": "How many sentences to include in the summary (1-10). Default 3.",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "web_search",
        "description": (
            "Search the web via DuckDuckGo and return up to N result snippets "
            "(title, url, snippet). Use when the question is recent, niche, "
            "or unlikely to be in Wikipedia."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query."},
                "max_results": {
                    "type": "integer",
                    "description": "Number of results to return (1-10). Default 5.",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "notes_add",
        "description": (
            "Append a research note to the user's local notes file. Use this "
            "to remember a finding the user explicitly asked to save."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Note content."},
            },
            "required": ["text"],
        },
    },
    {
        "name": "notes_list",
        "description": "List all notes the user has saved previously.",
        "parameters": {"type": "object", "properties": {}},
    },
]
