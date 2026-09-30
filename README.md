# get_apps

A pipeline for collecting and RAG-analyzing apps from the RuStore catalogue, driven entirely through a web UI (React + MUI).

1. **Collection** — crawl RuStore categories for app IDs, then scrape per-app metadata into SQLite.
2. **Indexing** — embed app descriptions locally and store the vectors in Chroma.
3. **Query** — ask natural-language questions; a local Ollama LLM answers from the indexed apps.

## Requirements

- **Python** 3.13+
- **Poetry** 2.0+
- **Node.js** 20.19+ or 22.12+, with **npm**
- **Ollama** — [ollama.com](https://ollama.com)
- **NVIDIA GPU** — recommended for embeddings (CUDA libraries are installed via pip). Without one, set the embedding device to `cpu` on the **Settings** page.
- **Chromium** — installed automatically by `make install`

## Setup

```bash
make install
```

Installs the Python dependencies, Chromium for Playwright, and the frontend npm packages.

### Models

Models are never downloaded automatically — install them yourself:

- **LLM**: `ollama pull gemma3:1b` (or any other model, then pick it on the **Settings** page). The backend starts `ollama serve` itself if it is not running, and checks for the model only at startup — restart the backend after pulling.
- **Embeddings** (`intfloat/multilingual-e5-large`, ~2 GB): click **Download** in the *Embedding Model* section of the **Settings** page. It is stored in `saved_data/cache/`.

## Running

### Development (hot reload)

```bash
make dev
```

- Backend: http://127.0.0.1:8000 (API docs at `/docs`)
- Frontend: http://localhost:5173

### Production (single port)

```bash
make build    # build the frontend into front/dist/
make start    # uvicorn serves both the API and the frontend on 127.0.0.1:8000
```

### Other commands

```bash
make format   # ruff format (backend) + prettier (frontend)
make clean    # remove the frontend build and Vite cache
```

## Web UI

- **Query** — RAG queries: pick a database, ask a question, get an answer with the applied filters and source apps.
- **Collection** — (1) collect `app_id`s by RuStore category, (2) scrape detailed app info into SQLite.
- **Indexing** — compute embeddings for the selected database and write them to Chroma.
- **Settings** — theme, Ollama model picker, embedding model download, and the runtime config editor (Ollama, embeddings, RAG, API).

Long-running tasks show live progress and logs over SSE. The header shows the backend, Ollama, and embedding model status.

## Configuration

Defaults live in `back/src/app/core/config.py`. Changes made on the **Settings** page are saved to `saved_data/config.json`. Values used at startup (Ollama URL, embedding model and device) require a backend restart.

## Project structure

```
back/                 # Python project (pyproject.toml, poetry.lock)
└── src/app/
    ├── main.py       # uvicorn entrypoint
    ├── api/          # FastAPI app factory, routes/ and schemas/ per domain
    ├── core/         # config, background jobs (SSE), db, chroma, embedder, ollama
    ├── models/       # ORM (AppInfo)
    ├── services/     # parsers, collection, indexing, retrieval, RAG
    └── tasks/        # coroutines wrapping each background job

front/                # React + Vite
└── src/              # Feature-Sliced Design: app / pages / widgets / features / entities / shared

saved_data/           # runtime data, not in git; created automatically
├── categories/<timestamp>/<category>.txt
├── databases/<name>.sqlite3
├── chroma/<name>/
├── cache/            # embedding model cache
└── config.json       # user config overrides
```
