# Journal — Step 3 (2026-05-15)

This entry covers testing, deployment preparation, and the data flow
between components.

## Testing process

Testing was performed **alongside** implementation: each tool was unit-
tested as soon as it was written, before being wired into the agent. The
agent loop was developed against a scripted fake `LLMClient` first; the
real `GeminiClient` was only plugged in after the loop's behaviour was
locked down by tests.

The full suite is run with:

```powershell
python -m pytest tests/
```

Current state: **31 tests, all passing in ~0.6 s.** None of the tests
require an API key or network access — Wikipedia and DuckDuckGo are
mocked, and the agent tests use a scripted fake LLM.

### Test scenarios and what they cover

**Calculator (13 tests)**

| Scenario | Expectation |
| --- | --- |
| Basic addition (`2 + 3`) | result `5`, `ok=True` |
| Operator precedence (`2 + 3 * 4`) | result `14` |
| Parentheses override precedence (`(2 + 3) * 4`) | result `20` |
| Power + unary minus | matches Python semantics |
| Allowed functions (`sqrt`, `sin`) | correct values |
| **Disallowed function** (`__import__('os').system(...)`) | rejected with `ok=False` |
| Empty input | rejected |
| Syntax error (`2 +`) | rejected |
| Division by zero | reported as error, not crashing |
| Parametrised table (5 cases) | each correct |

The disallowed-function test is the security-critical one: it confirms
the AST walker does not let arbitrary Python sneak through.

**Notes (5 tests)**

| Scenario | Expectation |
| --- | --- |
| Add two notes, then list | two notes with ids 1 and 2 |
| List with no file present | empty list, `ok=True` |
| Add empty / whitespace-only text | rejected |
| Strip whitespace around text | trailing/leading spaces removed |
| Corrupt JSON file | treated as empty; next write recovers |

**Wikipedia (4 tests, network mocked)**

| Scenario | Expectation |
| --- | --- |
| Happy path | summary + title + url returned |
| Empty query | rejected |
| Page not found | `ok=False`, helpful error message |
| Disambiguation page | falls back to first option, reports it via `note` |

**Web search (4 tests, DDGS mocked)**

| Scenario | Expectation |
| --- | --- |
| Happy path | results normalised to `{title, url, snippet}` |
| Empty query | rejected |
| `max_results=999` | clamped to 10 |
| Network error from DDGS | wrapped as `{"ok": False, "error": ...}` rather than raised |

**Agent loop (5 tests, fake LLM)**

| Scenario | Expectation |
| --- | --- |
| LLM returns text immediately | answer returned, trace has one final step |
| LLM calls calculator, then answers | tool ran, result forwarded back, final answer surfaced |
| LLM calls an unknown tool | `{"ok": False, "error": "unknown tool: ..."}` returned to LLM |
| LLM never finishes | loop stops after `max_steps`, `stopped_reason="max_steps"` |
| Empty user query | short-circuits without ever calling the LLM |

### Functional / manual testing

Beyond automated tests, the CLI was driven manually with `--trace`:

- `python main.py -q "What is sqrt(2) + 5?"` — model calls `calculator`,
  returns a numeric answer.
- `python main.py -q "Who is Alan Turing?"` — model calls
  `wikipedia_lookup`, summarises.
- `python main.py --interactive` followed by "Save a note: read about
  RAG" — model calls `notes_add`; next session, "what notes do I have?"
  calls `notes_list`.

These confirmed that the model actually selects the intended tool from
natural language and that results flow back correctly.

### Input validation testing

Every tool rejects empty/whitespace input with `ok=False` and an
explanation. The calculator additionally rejects any AST node it does
not whitelist. The agent rejects an empty user query without calling
the LLM. These cases are all asserted in the suite.

### Error-handling testing

Errors are caught at tool boundaries and converted to structured `error`
fields rather than raised. Tested directly for: calculator with bad
syntax / zero-division, wikipedia page-not-found, DDGS raising
mid-search, and the agent receiving an unknown tool name.

## Deployment preparation

The project is set up to be **installable and runnable by another user
with three commands and one secret**:

```powershell
git clone <repo-url>
cd ai-agent-task
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env  # then paste your Gemini API key
python main.py "Who invented the World Wide Web?"
```

Files supporting this:

- `requirements.txt` — pinned to minimum versions known to work.
- `.env.example` — every environment variable is listed with a
  description; sensitive values are not in version control (`.env` is
  gitignored).
- `README.md` — installation, configuration, usage, test instructions.
- `main.py` — single entry point with `--help`, `--interactive`,
  `--trace`.
- `config.py` — central place that translates env vars into a typed
  `Settings` object.

The `.env` file is the only thing a deployer must supply: it carries
`GEMINI_API_KEY` (required), and optionally `GEMINI_MODEL` and
`AGENT_MAX_STEPS`. Defaults are sane, so the optional ones can be left
unset.

## Data conversion / porting

Several components exchange data in different shapes. The agent treats
**every tool result as a `dict`** with a guaranteed `"ok"` key, so the
agent code itself never has to branch on tool identity.

Concrete conversions:

| Source | Shape | Where it's converted |
| --- | --- | --- |
| User CLI input | `str` | Passed unchanged to the agent. |
| Gemini `function_call` | proto buffer object with `.name`, `.args` | `GeminiClient._parse` converts each one into a `ToolCall(name, args)` dataclass; `args` is forced to a plain `dict`. |
| Tool result | tool-specific dict | The agent wraps it into `{"name": ..., "result": result}` and packs it into a `google.generativeai.protos.FunctionResponse` part before sending it back. |
| DuckDuckGo result | `{"title", "href", "body"}` | `web_search` renames `href → url` and `body → snippet` so the model sees consistent field names. |
| Wikipedia `Page` object | object with `.title`, `.url`, `.summary` | flattened into a plain dict by `wikipedia_lookup`. |
| Notes on disk | JSON array of `{id, timestamp, text}` | Read with `json.load`; appended to; written with `json.dump`. A corrupted file is treated as empty rather than crashing. |

Two things keep this consistent:

1. **Validation at boundaries.** Each tool checks its inputs and returns
   a structured error rather than raising. No partial state is ever
   persisted.
2. **A uniform return contract.** Every tool returns `{"ok": bool, ...}`.
   The agent and tests rely only on `ok`; tool-specific keys are only
   read by the LLM (via the JSON the agent ships back).

## Deployment strategy (proposed)

For a project at this scale, a **staged local-tool release** is the
right fit. Two stages:

1. **Local CLI distribution** *(current state).* Anyone with the repo,
   Python 3.10+, and a Gemini key can run it. Suitable for grading and
   for power users.

2. **Optional hardened release** *(future, not implemented).* If this
   were to be shared more widely, the next steps would be:
   - Add `pyproject.toml` so the project installs as a console script
     (`pip install .` exposes `research-agent` on `PATH`).
   - Pin every dependency in `requirements.txt` (currently I use `>=`
     for development convenience).
   - Add a GitHub Actions workflow that runs `pytest` on every push.
   - Ship a small Dockerfile so the deployment surface is "any host
     with Docker + an env var".

A **web service** deployment was considered (FastAPI in front of the
agent) but ruled out for this submission: it would add scope (auth,
rate limiting, deployment infrastructure) without strengthening the
core "tool-using agent" story that the assignment grades.
