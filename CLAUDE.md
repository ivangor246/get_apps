> **Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## About

Full-stack tool for collecting and analyzing app data from the RuStore catalogue, driven entirely through a web UI.

**Three core concerns:**
1. **Collection** — crawl the store by category, fetch per-app metadata, persist to SQLite.
2. **Indexing** — embed app descriptions into a Chroma vector store.
3. **RAG** — natural-language queries against the indexed data (retrieval + filter extraction + LLM answer).

All three are exposed as HTTP endpoints; there is no CLI. Long-running work runs as background jobs with live progress streamed over Server-Sent Events.

## Tech Stack

**Backend**
- **Python 3.14+**, async throughout (`asyncio`)
- **FastAPI + uvicorn** — sole entry point
- **Playwright** — headless browser for RuStore scraping
- **BeautifulSoup + lxml** — HTML parsing
- **SQLAlchemy (async) + aiosqlite** — ORM over SQLite
- **ChromaDB** — local persistent vector store
- **fastembed** — ONNX embeddings on CPU (`intfloat/multilingual-e5-large` by default)
- **Ollama** — LLM calls (via `httpx`)
- **Poetry** — dependency management
- **Ruff** — linting/formatting

**Frontend**
- **React 19 + TypeScript + Vite**
- **Material UI** (`@mui/material`) — Material Design components
- **React Router**, **@tanstack/react-query**
- **Feature-Sliced Design** layout

## Folder Structure

```
back/                              # Backend root (Poetry project)
├── pyproject.toml
├── poetry.lock
├── src/app/
│   ├── main.py                    # Thin uvicorn entrypoint
│   ├── api/                       # FastAPI app factory, routes, pydantic schemas
│   ├── core/                      # config, jobs (SSE), db, chroma, ollama, embedder
│   ├── tasks/                     # Async coroutines wrapping each collection / index run
│   ├── services/                  # Domain services (Rustore*, RAG, Retrieval, EmbeddingIndexer)
│   │   └── parsers/               # Playwright + BeautifulSoup page parsers
│   └── models/                    # SQLAlchemy ORM models
├── cache_dir/                     # fastembed / HuggingFace model cache
└── saved_data/
    ├── categories/{timestamp}/*.txt   # raw app IDs per category per run
    ├── databases/{name}.sqlite3       # collected app metadata, one DB per run set
    └── chroma/{name}/                 # persistent vector index, one dir per DB

front/src/                         # Feature-Sliced Design:
├── app/                           # App component + providers (theme, query client, router)
├── pages/                         # home, collection, indexing, settings
├── widgets/                       # app-header, db-selector, job-log-viewer
├── features/                      # toggle-theme, edit-config, run-*, submit-rag-query
├── entities/                      # config, database, job, rag-result
└── shared/                        # api client, SSE helper, theme, config
```

All Poetry/uvicorn commands run from `back/` (see `Makefile`).

## Architecture

**Backend layers:**
1. **API** (`api/`) — thin routes + pydantic schemas. Long-running work is dispatched to the job manager.
2. **Core** (`core/`) — config, job manager, shared clients (Ollama, embedder, Chroma, DB).
3. **Services** (`services/`) — domain logic: scraping, indexing, retrieval, RAG orchestration.
4. **Tasks** (`tasks/`) — async coroutines wiring services together for one run of a pipeline.

**Frontend (FSD):** strict unidirectional imports — `app → pages → widgets → features → entities → shared`. Cross-imports within the same slice go through the public `index.ts`.

**Adding a new store** = new parser + new service + new task + new endpoint + new feature/page on the frontend.

## Configuration

**Front and back are independent on configuration.** The backend owns hardcoded defaults in [back/src/app/core/config.py](back/src/app/core/config.py) and exposes them read-only via `GET /api/config`. The frontend fetches those defaults on load, lets the user edit tunable fields on the Settings page, and persists user overrides in **browser localStorage**. Each request from the frontend includes only the overrides relevant to that endpoint as **query parameters**; the backend never persists user-level config.

- Tunable per-request (sent as query params): `OLLAMA_LLM_MODEL`, `OLLAMA_TIMEOUT`, `OLLAMA_CONTEXT_SIZE`, `RAG_TOP_K`, `RAG_CANDIDATE_K`, `EMBEDDING_BATCH_SIZE`.
- Read-only (backend-startup, require code edit + restart): `OLLAMA_URL`, `EMBEDDING_MODEL`, `EMBEDDING_DIM`.
- Not exposed to UI: file paths, RuStore URLs + category list, pagination count, `API_HOST`/`API_PORT`.

## Background Jobs & SSE

Long-running endpoints (`POST /tasks/collect-categories`, `/tasks/collect-apps`, `/tasks/index`) return a `job_id` immediately. The client subscribes to `GET /tasks/{job_id}/events` (SSE) for live `log` / `progress` / `status` / `done` / `error` frames. Service-layer `logging.getLogger('app')` records are auto-forwarded to the job stream — services emit regular log calls, no job-aware plumbing required.

---

## Think Before Coding

Don't assume. Don't hide confusion. Surface tradeoffs.

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

---

## Code Style

Write professional, idiomatic code consistent with the language and ecosystem.

- Follow language-standard conventions (PEP 8, Airbnb JS, etc.).
- Use clear, descriptive names.
- Prefer explicit over implicit.
- Consistency with existing code overrides personal preference.
- Frontend: respect FSD import direction. Keep UI in `ui/`, data hooks in `model/`, public exports in `index.ts`.

---

## Comments & Documentation

**Comments** — only when necessary. Never explain the obvious.
Good comment: *why* the code does something non-obvious.
Bad comment: restating what the code already says.

**Docstrings / JSDoc / etc.** — required for every class, method, and function.
- Maximum 3 lines: purpose, key params/returns if non-obvious, notable caveats.
- Do not document anything else (variables, modules, type aliases, etc.).

---

## Simplicity First

Minimum code that solves the problem. Nothing speculative.

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

> Ask yourself: *"Would a senior engineer say this is overcomplicated?"* If yes, simplify.

---

## Surgical Changes

Touch only what you must. Clean up only your own mess.

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it — don't delete it.

When your changes create orphans:
- Remove imports / variables / functions that **your** changes made unused.
- Don't remove pre-existing dead code unless asked.

> **The test:** Every changed line should trace directly to the user's request.

---

## Goal-Driven Execution

Define success criteria. Loop until verified.

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass."
- "Fix the bug" → "Write a test that reproduces it, then make it pass."
- "Refactor X" → "Ensure tests pass before and after."

For multi-step tasks, state a brief plan before starting:

```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Weak success criteria ("make it work") require constant clarification — avoid them.

---

## Git

- **Never run git commands** (commit, push, rebase, etc.) without an explicit user request.
- At the end of every response that changes code, provide a short suggested commit message in a code block:

```
feat: add JWT refresh token rotation
```

---

## Error Handling

- Handle errors at the boundary where recovery or user feedback is meaningful.
- Don't swallow errors silently.
- Don't add error handling for states that cannot occur given the current design.

---

## Security & Safety

- Never hard-code secrets, API keys, or credentials — use environment variables or the runtime config store, not literals.
- Validate and sanitize all external input (user, API, file).
- Prefer well-maintained libraries over custom crypto or auth implementations.
- Flag security concerns explicitly rather than silently working around them.
