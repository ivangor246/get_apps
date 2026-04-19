# get_apps

Пайплайн для сбора и RAG-анализа приложений из RuStore.

## Требования

- **Python** 3.14+
- **Poetry** 2.0+
- **Ollama** (локально, для эмбеддингов и LLM) — [ollama.com](https://ollama.com)
- **Chromium** — ставится автоматически через `playwright install`

## Python-зависимости

Из [pyproject.toml](pyproject.toml):

- `beautifulsoup4`, `lxml` — парсинг HTML
- `playwright` — headless-браузер для обхода анти-бота RuStore
- `sqlalchemy[asyncio]`, `aiosqlite` — async ORM + SQLite-драйвер
- `httpx` — HTTP-клиент для Ollama
- `chromadb` — локальное persistent векторное хранилище (HNSW)
- `fastapi`, `uvicorn[standard]` — REST API для RAG

Dev: `ruff`.

## Установка

```bash
make install
```

Выполняет `poetry install` и ставит Chromium для Playwright.

## Модели Ollama

Перед индексацией и запуском API:

```bash
ollama pull bge-m3
ollama pull gemma4:e2b
ollama serve   # если не запущен как сервис
```

Имена моделей, URL Ollama и прочие настройки переопределяются переменными окружения
(см. [src/app/core/config.py](src/app/core/config.py)): `OLLAMA_URL`, `OLLAMA_LLM_MODEL`,
`OLLAMA_EMBEDDING_MODEL`, `EMBEDDING_DIM`, `RAG_TOP_K`, `RAG_CANDIDATE_K`,
`API_HOST`, `API_PORT`, `OLLAMA_TIMEOUT`.

## Команды

### Сбор app_id по категориям

```bash
make collect-categories
```

Результат: `saved_data/categories/<timestamp>/<category>.txt` — по одному файлу на категорию, один `app_id` на строку.

### Сбор детальной информации о приложениях

```bash
make collect-apps DB=<name> [FOLDER=<timestamp>] [CONCURRENCY=<N>]
```

- `DB` — имя SQLite-базы: сохранится в `saved_data/databases/<name>.sqlite3`.
- `FOLDER` — подпапка в `saved_data/categories/` (по умолчанию берётся самая свежая).
- `CONCURRENCY` — параллельные загрузки страниц (по умолчанию 3).

### Индексация эмбеддингов

```bash
make index DB=<name> [BATCH_SIZE=<N>]
```

Считает эмбеддинги `bge-m3` для каждого приложения без вектора и кладёт в Chroma-коллекцию `apps` в `saved_data/chroma/<name>/`. `BATCH_SIZE` по умолчанию 32.

### Запуск RAG API

```bash
make serve DB=<name> [HOST=<host>] [PORT=<port>]
```

Поднимает FastAPI на `127.0.0.1:8000` (по умолчанию).

**Эндпоинты:**

- `GET /health` — проверка живости.
- `POST /rag/query` — RAG-запрос.

Пример запроса:

```bash
curl -X POST http://127.0.0.1:8000/rag/query \
  -H 'Content-Type: application/json' \
  -d '{"query":"найди лучшие идеи приложений из приложений, у которых количество скачиваний выше чем медианное по базе, которые можно реализовать без сервера"}'
```

Ответ:

```json
{
  "answer": "...",
  "filters": { "above_median_downloads": true, "min_rating": null, "...": "..." },
  "sources": [ { "app_id": "...", "name": "...", "url": "...", "rating": 4.5, "downloads": 1000000, "categories": [...], "distance": 0.21 } ]
}
```

## Полный цикл

```bash
make install
ollama pull bge-m3 && ollama pull gemma4:e2b

make collect-categories
make collect-apps DB=rustore
make index DB=rustore
make serve DB=rustore
```

## CLI напрямую

Если удобнее без make:

```bash
poetry run python -m app.main categories
poetry run python -m app.main apps   --db <name> [--folder <ts>] [--concurrency 3]
poetry run python -m app.main index  --db <name> [--batch-size 32]
poetry run python -m app.main serve  --db <name> [--host 127.0.0.1] [--port 8000]
```

## Структура

```
src/app/
├── main.py                 # CLI
├── api/                    # FastAPI (create_app, routes, schemas)
├── core/                   # config, db, ollama, chroma
├── models/                 # ORM (AppInfo)
├── services/               # парсеры, сбор, индексация, retrieval, RAG
└── tasks/                  # точки входа CLI для каждой команды

saved_data/
├── categories/<timestamp>/<category>.txt
├── databases/<name>.sqlite3
└── chroma/<name>/          # persistent Chroma-хранилище эмбеддингов
```
