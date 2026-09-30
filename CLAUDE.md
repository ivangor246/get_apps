## About

Web UI tool for collecting and analyzing RuStore catalogue data. No CLI — everything goes through FastAPI endpoints driven by the React frontend.

1. **Collection** — Playwright crawls categories → app IDs → per-app metadata → SQLite.
2. **Indexing** — descriptions embedded with fastembed (ONNX, GPU) into Chroma.
3. **RAG** — retrieval + filter extraction + answer via a local Ollama LLM.

**Stack:** Python 3.14, FastAPI, Playwright + BeautifulSoup, async SQLAlchemy/aiosqlite, ChromaDB, fastembed-gpu, Ollama over `httpx`, Poetry, Ruff · React 19, TypeScript, Vite, MUI 6, React Router, TanStack Query, Feature-Sliced Design.

## Commands

```bash
make install        # poetry install + playwright chromium + npm install
make dev            # backend :8000 (reload) + frontend :5173
make build          # build front/dist (served by the backend in `make start`)

poetry run ruff check src && poetry run ruff format src
npm --prefix front run lint
npm --prefix front run build   # includes tsc type-check
```

There is no test suite. Verify changes with ruff + frontend lint/build, and state what you could not verify (scraping, GPU, Ollama need the real environment).

The user runs install/dependency/server commands themselves: propose `poetry add`, `npm install`, `make dev` etc. as code blocks instead of executing them.

## Layout

```
src/app/
├── main.py      # uvicorn entrypoint (`make start`)
├── api/         # app factory (lifespan builds Ollama client + embedder), routes.py, schemas.py
├── core/        # config, jobs (SSE), db, chroma, embedder, ollama (LLM), ollama_runtime (model list/load)
├── services/    # domain logic: Rustore*, EmbeddingIndexer, Retrieval, RAG; parsers/ = page parsers
├── tasks/       # one coroutine per pipeline run, wiring services together
└── models/      # SQLAlchemy ORM

front/src/       # FSD: app → pages → widgets → features → entities → shared

saved_data/
├── categories/{timestamp}/*.txt   # app IDs per category per run
├── databases/{name}.sqlite3       # collected metadata
├── chroma/{name}/                 # vector index, one per database
└── config.json                    # user config overrides
```

**New store** = parser + service + task + endpoint + frontend feature/page.

## Configuration

No `.env`. Defaults live in [src/app/core/config.py](src/app/core/config.py): fields with `init=True` on `Config` are tunable from the Settings page and persisted to `saved_data/config.json`; `init=False` fields (paths, RuStore URLs/categories, page count) are code-only.

- `get_config()` returns fresh values after a save; the module-level `config` is a snapshot taken at import. Read tunable values via `get_config()` at call time.
- Clients built in the app lifespan (Ollama base URL/timeout, embedder model/device) only pick up changes after a backend restart.

## Background jobs

`POST /tasks/{collect-categories,collect-apps,index}` return a `job_id`; the client streams `GET /tasks/{job_id}/events` (SSE: `log` / `progress` / `status` / `done` / `error`) and can `POST /tasks/{job_id}/cancel`. Records logged to `logging.getLogger('app')` (and children) during a job are forwarded to its stream automatically — services just log, no job plumbing.

---

## Working rules

- **Ask when ambiguous.** State assumptions; if there are several readings of the request, list them instead of picking one silently. Push back if a simpler approach exists.
- **Minimal and surgical.** Implement only what was asked: no speculative options, abstractions for single use, or handling of impossible states. Don't touch unrelated code — mention dead code or bugs you notice instead of fixing them. Remove only the orphans your own change created.
- **Plan multi-step work** briefly as `step → how it will be verified` before starting.
- **Errors** are handled where recovery or user feedback is meaningful (routes, job boundaries); never swallowed silently.
- **Security:** no secrets in code or `config.json` defaults; validate external input (request bodies, scraped HTML, LLM output) at the boundary; flag concerns explicitly.

## Code style

- Consistency with surrounding code beats personal preference.
- Python: Ruff, line length 120, single quotes, async throughout. Python 3.14 syntax is intentional (e.g. `except A, B:` without parentheses) — don't "fix" it.
- Frontend: respect FSD import direction; cross-slice imports only via the slice's `index.ts`. UI in `ui/`, data hooks/queries in `model/`, API calls through `shared/api`.
- Comments only for non-obvious *why*.
- Docstrings/JSDoc are required on every class, method and function, max 3 lines (purpose, non-obvious params/returns, caveats). Nothing else gets documented.

## Git

- Never run git commands unless explicitly asked.
- End every response that changes code with a suggested Conventional Commit message in a code block, scoped like the existing history:

```
feat(ollama): make context size configurable via model picker
```
