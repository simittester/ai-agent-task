"""CLI entry point for the AI Research Assistant.

Usage examples:
    python main.py "Who invented the World Wide Web?"
    python main.py --interactive
    python main.py -q "What is sqrt(2) + 5?" --trace
"""

from __future__ import annotations

import argparse
import sys
from typing import List

from config import load_settings
from src.agent import AgentResult, ResearchAgent
from src.llm import GeminiClient
from src.tools import TOOL_SCHEMAS


def _build_agent() -> ResearchAgent:
    settings = load_settings()
    llm = GeminiClient(
        api_key=settings.gemini_api_key,
        model_name=settings.gemini_model,
        tool_schemas=TOOL_SCHEMAS,
    )
    return ResearchAgent(llm=llm, max_steps=settings.agent_max_steps)


def _print_result(result: AgentResult, show_trace: bool) -> None:
    if show_trace:
        print("--- trace ---")
        for i, step in enumerate(result.trace, 1):
            if step.kind == "tool_call":
                print(f"[{i}] tool: {step.tool_name}({step.tool_args})")
                print(f"    -> {step.tool_result}")
            else:
                print(f"[{i}] final: {step.text[:120]}{'...' if len(step.text) > 120 else ''}")
        print("--- /trace ---\n")
    print(result.answer)


def _interactive(agent: ResearchAgent, show_trace: bool) -> None:
    print("Research Assistant (type 'exit' or Ctrl-C to quit)")
    try:
        while True:
            try:
                q = input("\n> ").strip()
            except EOFError:
                return
            if not q:
                continue
            if q.lower() in {"exit", "quit"}:
                return
            result = agent.run(q)
            print()
            _print_result(result, show_trace)
    except KeyboardInterrupt:
        print()
        return


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AI Research Assistant")
    parser.add_argument("query", nargs="*", help="Question to ask. If omitted, use -i or --query.")
    parser.add_argument("-q", "--query", dest="query_flag", help="Question to ask (alternative to positional).")
    parser.add_argument("-i", "--interactive", action="store_true", help="Open a REPL.")
    parser.add_argument("--trace", action="store_true", help="Print the tool-call trace before the answer.")
    args = parser.parse_args(argv)

    try:
        agent = _build_agent()
    except ValueError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2

    if args.interactive:
        _interactive(agent, show_trace=args.trace)
        return 0

    query = args.query_flag or " ".join(args.query).strip()
    if not query:
        parser.print_help()
        return 1

    result = agent.run(query)
    _print_result(result, show_trace=args.trace)
    return 0


if __name__ == "__main__":
    sys.exit(main())
