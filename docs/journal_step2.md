# Journal - Step 2 (2026-05-08)

## Updated system description

The system has moved from plan to working code. The core is implemented:

- `src/agent.py` — the `ResearchAgent` class with a clean tool-call loop
  bounded by `AGENT_MAX_STEPS`.
- `src/llm.py` — an `LLMClient` protocol plus a concrete `GeminiClient`.
  Splitting the protocol off was a deliberate decision so the agent loop
  can be tested with a scripted fake LLM, with no API key needed.
- `src/tools/` — five tools plus a registry. Each tool is a pure function
  that returns a JSON-serialisable dict with the same shape.
- `main.py` — a CLI with one-shot mode, interactive REPL, and a `--trace`
  option.

The structural shape from Step 1 mostly held. Two refinements emerged
during implementation:

1. **Tool registry vs. ad-hoc imports.** I considered hard-coding the tool
   list inside the agent, but pulling it into `src/tools/__init__.py`
   means I can add a tool by touching one file. The registry exposes
   `TOOLS` (the callable map) and `TOOL_SCHEMAS` (the JSON schemas Gemini
   needs). Both are kept side-by-side so they cannot drift.
2. **Aliased re-exports.** The first version of `src/tools/__init__.py`
   re-exported each tool function under its own name (`from .web_search
   import web_search`). That shadowed the submodule attribute on the
   package and broke `import src.tools.web_search` in tests. I now import
   each tool under a private alias (`_web_search`), which keeps the
   submodule names intact.

## Refined list of programming concepts (actually used)

- **Packages and `__init__.py`** for clean module boundaries.
- **`@dataclass(frozen=True)`** for the `Settings` config object so it
  cannot be mutated at runtime.
- **`typing.Protocol`** for the `LLMClient` interface — gives me
  structural typing without an inheritance dependency.
- **`ast.parse(..., mode="eval")`** with a recursive walker for the
  calculator. The walker only allows a whitelisted set of node types
  (`BinOp`, `UnaryOp`, `Constant`, `Call` with a whitelisted function
  name). Everything else raises `ValueError`. This makes the tool safe
  to call on untrusted strings.
- **`pathlib.Path`** end-to-end instead of `os.path` string juggling.
- **Context managers** (`with open(...)`, `with DDGS() as ddgs:`).
- **JSON serialisation** for notes.
- **`argparse`** for the CLI.
- **`pytest` fixtures** (`tmp_path`) and `monkeypatch` for mocking
  modules (the wikipedia and DDGS calls).
- **Exception chaining contained at boundaries** — tools catch their own
  errors and convert them to `{"ok": False, "error": "..."}` rather than
  letting them escape into the agent.

## How tools are integrated

Each tool is a normal Python function with two-fold metadata:

1. A **runtime mapping** in `TOOLS` (`name → callable`).
2. A **JSON-schema declaration** in `TOOL_SCHEMAS` (matching Gemini's
   function-declaration format).

At startup, `GeminiClient` passes the schemas to the model. When the
model emits a `function_call`, the agent looks the name up in `TOOLS`,
unpacks the args, calls the function, and wraps the result in a
`function_response` part that goes back to the model. The agent does not
need to know what any tool does — only how to dispatch a call and a
result.

All tools return the same dict shape (`{"ok": bool, ...}`). This
uniformity is intentional: it means the agent loop can blindly forward
tool results, and tests can assert on `ok` without remembering which key
each tool uses for its payload.
