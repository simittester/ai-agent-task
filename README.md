# AI Research Assistant

A small Python project that implements an **AI-assisted, tool-using agent**.
The agent receives a natural-language question, decides which tools to call,
executes them, and returns a concise answer.

It is a single-agent system powered by Google's **Gemini** model
(`gemini-flash-latest`, free tier). The model performs the reasoning; the
project supplies the tools, the agent loop, configuration, tests, and a CLI.

---

## What the agent can do

The agent has access to five tools:

| Tool | Purpose |
| --- | --- |
| `calculator` | Safely evaluate arithmetic expressions (no `eval`; AST-walked whitelist of operators and math functions). |
| `wikipedia_lookup` | Fetch a short summary of a topic from English Wikipedia (no key — Wikipedia's public API is open). |
| `web_search` | Search the web through DuckDuckGo (no key — DuckDuckGo is keyless; the `ddgs` library queries the public results page). |
| `notes_add` | Append a note to a local JSON file (`data/notes.json`). |
| `notes_list` | List all saved notes. |

The model receives JSON schemas describing each tool. It picks tools by name,
fills in their arguments, and the agent executes them and feeds results back
until the model produces a final natural-language answer.

### What needs an API key, and what does not

The project uses **exactly one** API key in total: `GEMINI_API_KEY`, for the
LLM at the top of the system. None of the five tools require their own
keys — Wikipedia and DuckDuckGo both expose keyless endpoints, the
calculator runs in-process, and the notes tool reads/writes a local file.
See [Configuration](#configuration) below for how to set the Gemini key.

---

## Project layout

```
ai-agent-task/
├── main.py                 # CLI entry point
├── config.py               # Settings + env loading
├── requirements.txt
├── .env.example            # Template for the API key
├── .gitignore
├── README.md
├── src/
│   ├── agent.py            # ResearchAgent: the tool-using loop
│   ├── llm.py              # Gemini client + LLMClient protocol
│   └── tools/
│       ├── __init__.py     # Tool registry + JSON schemas
│       ├── calculator.py
│       ├── notes.py
│       ├── web_search.py
│       └── wikipedia_lookup.py
├── tests/
│   ├── conftest.py
│   ├── test_agent.py       # Agent loop tests (fake LLM)
│   ├── test_calculator.py
│   ├── test_notes.py
│   ├── test_web_search.py  # DDGS mocked
│   └── test_wikipedia.py   # wikipedia module mocked
├── data/                   # Runtime data (notes.json created on first write)
└── docs/
    ├── journal_step1.md
    ├── journal_step2.md
    └── journal_step3.md
```

---

## Installation

**Prerequisites:** Python 3.10 or newer.

```powershell
git clone https://github.com/<your-username>/ai-agent-task.git
cd ai-agent-task

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

(On macOS/Linux: `source .venv/bin/activate`.)

---

## Configuration

1. Get a free Gemini API key at <https://aistudio.google.com/app/apikey>.
2. Copy `.env.example` to `.env` and paste your key:

```
GEMINI_API_KEY=AIzaSy...your-key...
GEMINI_MODEL=gemini-flash-latest
AGENT_MAX_STEPS=6
```

| Variable | Default | Meaning |
| --- | --- | --- |
| `GEMINI_API_KEY` | *(required)* | Your Gemini key. |
| `GEMINI_MODEL` | `gemini-flash-latest` | Model name. `gemini-flash-latest` is free for every account; some newer accounts do not get free-tier access to `gemini-2.0-flash`. |
| `AGENT_MAX_STEPS` | `6` | Cap on tool-call rounds before the loop bails out. |

---

## Running the assistant

**One-shot question:**

```powershell
python main.py "Who invented the World Wide Web?"
python main.py -q "What is sqrt(2) plus 5?"
python main.py "Summarize Marie Curie" --trace
```

`--trace` prints every tool call the agent made and its result, before the
final answer — useful for understanding what the agent did.

**Interactive REPL:**

```powershell
python main.py --interactive
```

Type questions one per line. `exit` or Ctrl-C to quit.

---

## Running the tests

```powershell
$env:PYTHONPATH = "."
python -m pytest tests/ -v
```

There are **31 tests** covering:

- Calculator: arithmetic, precedence, allowed functions, rejection of
  arbitrary Python, syntax errors, division-by-zero.
- Notes: add/list round-trip, missing file, empty input, whitespace
  stripping, corrupt-file recovery.
- Wikipedia: happy path, missing page, disambiguation fallback (network
  mocked).
- Web search: happy path, max-results clamp, error wrapping (DuckDuckGo
  mocked).
- Agent loop: immediate answer, single tool call, unknown tool handling,
  max-step loop breaker, empty-query short-circuit (LLM faked).

Mocking the LLM means **no Gemini API key is required to run the tests** —
the test suite is fully offline.

---

## How the data flows

1. **User input** (string) arrives via CLI args or REPL.
2. The agent sends it to Gemini together with JSON schemas for all tools.
3. Gemini returns either text (a final answer) **or** a list of structured
   `function_call` objects: `{name, args}`.
4. For each tool call the agent looks up the function in `TOOLS`, calls it
   with `**args`, and gets back a dict like `{"ok": True, "result": ...}`.
5. The agent wraps each result in a `function_response` part and sends them
   back to the model.
6. The model either calls more tools or emits a final text answer; the loop
   stops on the first text-only response (or after `AGENT_MAX_STEPS`).

Every tool returns a **uniform dict shape** (`ok: bool`, plus tool-specific
keys, or `error: str` on failure) so the agent does not need to know
tool-specific details. Notes are persisted to disk as a list of JSON
objects with `id`, `timestamp`, `text`.

---

## Deployment

This is designed as a **local command-line tool**. To run it on another
machine someone needs only:

1. Python 3.10+.
2. `git clone` and `pip install -r requirements.txt`.
3. A `.env` with a Gemini key.

A staged release strategy is described in
[docs/journal_step3.md](docs/journal_step3.md).

---

## License

MIT.
