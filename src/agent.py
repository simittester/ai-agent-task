"""ResearchAgent: a single agent that uses tools to answer questions.

The loop:
    1. Send the user's question to the LLM together with the tool schemas.
    2. If the LLM responds with tool calls, execute each one and send the
       results back. Otherwise, return the LLM's final text answer.
    3. Repeat up to `max_steps` rounds before giving up.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from src.llm import LLMClient
from src.tools import TOOLS


SYSTEM_PROMPT = """You are a careful research assistant.

You have access to tools: calculator, wikipedia_lookup, web_search, notes_add,
notes_list. Use them whenever the answer requires facts you might not know,
arithmetic, or saving/retrieving a user's notes. Prefer wikipedia_lookup for
well-known topics and web_search for recent or niche queries. Use calculator
for any numeric computation rather than guessing.

When you have enough information, write a concise final answer in plain text
(no tool call). Cite tool results inline where useful (e.g. "according to
Wikipedia, ..."). If a tool returns an error, explain what failed and try a
sensible alternative."""


@dataclass
class TraceStep:
    """One round of the agent loop, captured for inspection and tests."""
    kind: str  # "tool_call" | "final"
    tool_name: str = ""
    tool_args: Dict[str, Any] = field(default_factory=dict)
    tool_result: Dict[str, Any] = field(default_factory=dict)
    text: str = ""


@dataclass
class AgentResult:
    answer: str
    trace: List[TraceStep]
    stopped_reason: str  # "final" | "max_steps" | "no_response"


class ResearchAgent:
    def __init__(self, llm: LLMClient, max_steps: int = 6):
        self.llm = llm
        self.max_steps = max_steps

    def run(self, user_query: str) -> AgentResult:
        if not isinstance(user_query, str) or not user_query.strip():
            return AgentResult(
                answer="Please provide a non-empty question.",
                trace=[],
                stopped_reason="final",
            )

        trace: List[TraceStep] = []
        response = self.llm.start(SYSTEM_PROMPT, user_query)

        for _ in range(self.max_steps):
            if response.is_final:
                final = response.text or ""
                trace.append(TraceStep(kind="final", text=final))
                return AgentResult(answer=final, trace=trace, stopped_reason="final")

            tool_results: List[Dict[str, Any]] = []
            for call in response.tool_calls:
                result = self._execute(call.name, call.args)
                trace.append(TraceStep(
                    kind="tool_call",
                    tool_name=call.name,
                    tool_args=call.args,
                    tool_result=result,
                ))
                tool_results.append({"name": call.name, "result": result})

            response = self.llm.send_tool_results(tool_results)

        # Loop fell through — capture whatever the model said last.
        fallback = response.text or "(no final answer; agent hit max_steps)"
        trace.append(TraceStep(kind="final", text=fallback))
        return AgentResult(answer=fallback, trace=trace, stopped_reason="max_steps")

    @staticmethod
    def _execute(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        tool = TOOLS.get(name)
        if tool is None:
            return {"ok": False, "error": f"unknown tool: {name}"}
        try:
            return tool(**args)
        except TypeError as exc:
            return {"ok": False, "error": f"bad arguments for {name}: {exc}"}
        except Exception as exc:  # noqa: BLE001 — tool boundary
            return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
