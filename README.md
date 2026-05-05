# get_apps

Пайплайн для сбора и RAG-анализа приложений из RuStore. Управление — через веб-интерфейс (React + MUI).

## Требования

- **Python** 3.14+
- **Poetry** 2.0+
- **Node.js** 20+ / **npm**
- **Ollama** (локально, для LLM) — [ollama.com](https://ollama.com)
- **Chromium** — ставится автоматически через `playwright install`

## Установка

```bash
make install
```

Ставит python-зависимости, Chromium для Playwright и npm-пакеты фронтенда.

## Модели Ollama

```bash
ollama pull <model>   # любая модель на ваш выбор, например llama3.2:3b
ollama serve          # если не запущен как сервис
```

Активная LLM выбирается на фронтенде в виджете AI Model и сохраняется в localStorage браузера; бэкенд не имеет модели по умолчанию.

Эмбеддинги считаются локально через `fastembed` на CPU (`intfloat/multilingual-e5-large`). Дефолты конфига живут в [back/src/app/core/config.py](back/src/app/core/config.py); фронт читает их из `GET /api/config`, тюнабельные значения редактируются в UI на странице **Settings** и хранятся в localStorage браузера, передаваясь в запросы как query-параметры.

## Запуск

### Разработка (бэкенд + фронтенд с hot-reload)

```bash
make dev
```

- Backend: http://127.0.0.1:8000
- Frontend: http://localhost:5173

### Продакшен (единый порт)

```bash
make build    # собрать фронт в front/dist/
make start    # uvicorn отдаёт и API, и статику фронта на 127.0.0.1:8000
```

## Веб-интерфейс

- **Query** — RAG-запросы: выбор БД, естественно-языковой вопрос, ответ + применённые фильтры + source-apps.
- **Collection** — (1) сбор `app_id` по категориям RuStore, (2) сбор детальной информации в SQLite.
- **Indexing** — расчёт эмбеддингов по выбранной БД и запись в Chroma.
- **Settings** — переключение темы (light/dark) + редактор runtime-конфига (Ollama, embedding, RAG, API).

Все длительные задачи показывают живой прогресс и логи через SSE.

## Структура

```
back/                              # бэкенд (Poetry-проект)
├── pyproject.toml
├── poetry.lock
├── src/app/
│   ├── main.py                    # uvicorn entrypoint
│   ├── api/                       # FastAPI (create_app, routes, schemas)
│   ├── core/                      # config, jobs (SSE), db, ollama, chroma, embedder
│   ├── models/                    # ORM (AppInfo)
│   ├── services/                  # парсеры, сбор, индексация, retrieval, RAG
│   └── tasks/                     # корутины-обёртки для фоновых задач
├── cache_dir/                     # кэш моделей fastembed / HuggingFace
└── saved_data/
    ├── categories/<timestamp>/<category>.txt
    ├── databases/<name>.sqlite3
    └── chroma/<name>/

front/src/                         # FSD: app / pages / widgets / features / entities / shared
```
