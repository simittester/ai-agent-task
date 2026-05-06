"""End-to-end agent tests using a scripted fake LLM."""

from typing import Any, Dict, List

from src.agent import ResearchAgent
from src.llm import LLMResponse, ToolCall


class FakeLLM:
    """A scripted LLM: returns the next item from `script` on each call."""

    def __init__(self, script: List[LLMResponse]):
        self._script = list(script)
        self.start_calls: List[Dict[str, str]] = []
        self.tool_result_calls: List[List[Dict[str, Any]]] = []

    def start(self, system_prompt: str, user_message: str) -> LLMResponse:
        self.start_calls.append({"system": system_prompt, "user": user_message})
        return self._next()

    def send_tool_results(self, results):
        self.tool_result_calls.append(results)
        return self._next()

    def _next(self) -> LLMResponse:
        if not self._script:
            return LLMResponse(text="(script exhausted)", tool_calls=[])
        return self._script.pop(0)


def test_immediate_final_answer():
    llm = FakeLLM([LLMResponse(text="Paris.", tool_calls=[])])
    agent = ResearchAgent(llm=llm, max_steps=4)
    result = agent.run("What is the capital of France?")
    assert result.answer == "Paris."
    assert result.stopped_reason == "final"
    assert len(result.trace) == 1
    assert result.trace[0].kind == "final"


def test_calculator_tool_call_then_answer():
    llm = FakeLLM([
        LLMResponse(text=None, tool_calls=[ToolCall("calculator", {"expression": "2 + 2"})]),
        LLMResponse(text="The answer is 4.", tool_calls=[]),
    ])
    agent = ResearchAgent(llm=llm, max_steps=4)
    result = agent.run("What is 2 + 2?")
    assert result.answer == "The answer is 4."
    assert result.stopped_reason == "final"
    assert result.trace[0].kind == "tool_call"
    assert result.trace[0].tool_name == "calculator"
    assert result.trace[0].tool_result["result"] == 4
    # The agent must forward the tool result back to the LLM.
    assert len(llm.tool_result_calls) == 1
    assert llm.tool_result_calls[0][0]["result"]["result"] == 4


def test_unknown_tool_is_handled():
    llm = FakeLLM([
        LLMResponse(text=None, tool_calls=[ToolCall("not_a_tool", {})]),
        LLMResponse(text="Sorry, I could not solve that.", tool_calls=[]),
    ])
    agent = ResearchAgent(llm=llm, max_steps=4)
    result = agent.run("anything")
    assert result.trace[0].tool_result["ok"] is False
    assert "unknown tool" in result.trace[0].tool_result["error"]


def test_max_steps_loop_breaker():
    # The fake never returns final; the agent must stop at max_steps.
    forever = [
        LLMResponse(text=None, tool_calls=[ToolCall("calculator", {"expression": "1 + 1"})])
        for _ in range(10)
    ]
    llm = FakeLLM(forever)
    agent = ResearchAgent(llm=llm, max_steps=3)
    result = agent.run("loop forever")
    assert result.stopped_reason == "max_steps"
    # Exactly max_steps tool rounds + 1 final fallback entry.
    tool_steps = [s for s in result.trace if s.kind == "tool_call"]
    assert len(tool_steps) == 3


def test_empty_query_short_circuits():
    llm = FakeLLM([])  # should never be called
    agent = ResearchAgent(llm=llm, max_steps=4)
    result = agent.run("   ")
    assert result.stopped_reason == "final"
    assert llm.start_calls == []
