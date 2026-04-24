# Journal — Step 1 (2026-04-24)

## Planned system and goal

I will build a small **AI Research Assistant** in Python. The goal is to
let a user ask a research-style question in natural language and have a
single AI-driven agent decide which tools to call to answer it.

The system addresses a practical problem: most quick "research" questions
need a mix of factual lookup (Wikipedia or the web), arithmetic, and the
ability to save findings for later. Doing this manually means hopping
between a browser, a calculator, and a notes app. A tool-using agent can
do it in one prompt.

## AI / agent-based approach

The system will be a **single intelligent agent** powered by an LLM. The
LLM acts as the planner: given the user's question and a list of available
tools, it decides which tool to call, with which arguments. The agent
executes the tool, feeds the result back to the LLM, and loops until the
LLM produces a final answer.

I chose a single-agent design rather than a multi-agent workflow because:

- the task complexity does not justify multiple agents,
- it is far easier to test a single deterministic loop,
- it keeps the focus on **tool use**, which is the stated requirement.

The LLM will be **Google Gemini** (`gemini-2.0-flash`) via the free tier of
`google-generativeai`. Gemini has solid function-calling support and the
free tier is enough for development and grading.

## Planned tools

| Tool | What it does |
| --- | --- |
| `calculator` | Evaluate arithmetic expressions safely. |
| `wikipedia_lookup` | Fetch a short Wikipedia summary. |
| `web_search` | DuckDuckGo search (no key). |
| `notes_add` | Append a note to a local JSON file. |
| `notes_list` | Read back all saved notes. |

This mix covers: computation, factual lookup with a structured source,
fallback web search, and a local-file I/O tool. That hits four very
different tool categories with a small surface area.

## Preliminary list of programming concepts

- **Modules and packages** for project structure.
- **Functions** as the tool unit, all with the same return contract.
- **Dataclasses** for typed value objects (`Settings`, `LLMResponse`,
  `ToolCall`, `TraceStep`, `AgentResult`).
- **Protocols** (`typing.Protocol`) to decouple the agent from the LLM.
- **AST parsing** (Python's `ast` module) to build a safe calculator
  without `eval`.
- **File I/O + JSON** for the notes tool.
- **Environment configuration** via `python-dotenv`.
- **Error handling** at the tool boundary so a single bad tool call never
  crashes the agent.
- **Unit and integration testing** with `pytest`, including
  `monkeypatch` for the network-touching tools.
- **CLI handling** with `argparse`.
- **Version control** with Git, with a clear progression of commits.
