"""Gemini LLM wrapper.

The agent talks to LLMs through a tiny protocol (`LLMClient`) so tests can
substitute a scripted fake. Only `GeminiClient` performs real API calls.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol


@dataclass
class ToolCall:
    """A single tool invocation requested by the model."""
    name: str
    args: Dict[str, Any]


@dataclass
class LLMResponse:
    """One step in the conversation: either tool calls, or final text."""
    text: Optional[str]
    tool_calls: List[ToolCall]

    @property
    def is_final(self) -> bool:
        return not self.tool_calls


class LLMClient(Protocol):
    def start(self, system_prompt: str, user_message: str) -> LLMResponse: ...
    def send_tool_results(self, results: List[Dict[str, Any]]) -> LLMResponse: ...


class GeminiClient:
    """Adapter over google-generativeai's chat + function-calling API."""

    def __init__(self, api_key: str, model_name: str, tool_schemas: List[Dict[str, Any]]):
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is not set. Copy .env.example to .env and add your key."
            )
        import google.generativeai as genai  # type: ignore[import-not-found]

        self._genai = genai
        genai.configure(api_key=api_key)
        self._tool_schemas = tool_schemas
        self._model_name = model_name
        self._model = genai.GenerativeModel(
            model_name=model_name,
            tools=[{"function_declarations": tool_schemas}],
        )
        self._chat = None  # created on first call so the system prompt lands

    def start(self, system_prompt: str, user_message: str) -> LLMResponse:
        self._model = self._genai.GenerativeModel(
            model_name=self._model_name,
            tools=[{"function_declarations": self._tool_schemas}],
            system_instruction=system_prompt,
        )
        self._chat = self._model.start_chat()
        resp = self._chat.send_message(user_message)
        return self._parse(resp)

    def send_tool_results(self, results: List[Dict[str, Any]]) -> LLMResponse:
        if self._chat is None:
            raise RuntimeError("send_tool_results called before start")
        genai = self._genai
        parts = [
            genai.protos.Part(
                function_response=genai.protos.FunctionResponse(
                    name=r["name"],
                    response={"result": r["result"]},
                )
            )
            for r in results
        ]
        content = genai.protos.Content(role="user", parts=parts)
        resp = self._chat.send_message(content)
        return self._parse(resp)

    @staticmethod
    def _parse(response: Any) -> LLMResponse:
        tool_calls: List[ToolCall] = []
        text_chunks: List[str] = []
        for cand in response.candidates:
            for part in cand.content.parts:
                fc = getattr(part, "function_call", None)
                if fc and getattr(fc, "name", ""):
                    args = dict(fc.args) if fc.args else {}
                    tool_calls.append(ToolCall(name=fc.name, args=args))
                else:
                    text = getattr(part, "text", "")
                    if text:
                        text_chunks.append(text)
        return LLMResponse(
            text="\n".join(text_chunks) if text_chunks else None,
            tool_calls=tool_calls,
        )
