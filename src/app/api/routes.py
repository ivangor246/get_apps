from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.core.config import get_config, get_tunable_defaults, settings_store
from app.core.jobs import JobManager
from app.services import RAGService
from app.tasks.index import run_index_task
from app.tasks.rustore import run_rustore_tasks
from app.tasks.rustore_app_info import run_rustore_app_info_tasks

from .schemas import (
    AppConfig,
    AppConfigPatch,
    AppliedFilters,
    CategoriesRunsResponse,
    CollectAppsRequest,
    CollectCategoriesRequest,
    DatabasesResponse,
    IndexRequest,
    JobCreated,
    JobSnapshot,
    OllamaStatusSchema,
    RAGQueryRequest,
    RAGQueryResponse,
    SourceApp,
    SystemStatusSchema,
)

router = APIRouter()


def _jobs(request: Request) -> JobManager:
    return request.app.state.jobs


@router.get('/health')
async def health() -> dict:
    """Liveness probe."""
    return {'status': 'ok'}


@router.get('/status', response_model=SystemStatusSchema)
async def system_status(request: Request) -> SystemStatusSchema:
    """Aggregated backend + Ollama runtime status for the UI status indicator."""
    state = request.app.state.ollama_runtime.state
    return SystemStatusSchema(
        backend='ready',
        ollama=OllamaStatusSchema(
            status=state.status.value,
            detail=state.detail,
            model=state.model,
        ),
    )


@router.get('/config', response_model=AppConfig)
async def read_config() -> AppConfig:
    """Return current effective config (defaults merged with saved overrides)."""
    cfg = get_config()
    return AppConfig(**{k: getattr(cfg, k) for k in get_tunable_defaults().keys()})


@router.put('/config', response_model=AppConfig)
async def write_config(patch: AppConfigPatch) -> AppConfig:
    """Merge patch into saved overrides; persists to saved_data/config.json."""
    existing = settings_store.load()
    updates = patch.model_dump(exclude_unset=True, exclude_none=False)
    merged = {**existing, **updates}
    settings_store.save(merged)
    cfg = get_config()
    return AppConfig(**{k: getattr(cfg, k) for k in get_tunable_defaults().keys()})


@router.get('/config/defaults', response_model=AppConfig)
async def read_config_defaults() -> AppConfig:
    """Return hardcoded defaults (ignoring any saved overrides)."""
    return AppConfig(**get_tunable_defaults())


@router.get('/databases', response_model=DatabasesResponse)
async def list_databases() -> DatabasesResponse:
    """List SQLite databases under saved_data/databases/ (by stem name)."""
    cfg = get_config()
    cfg.DATABASES_DIR.mkdir(parents=True, exist_ok=True)
    names = sorted(p.stem for p in cfg.DATABASES_DIR.glob('*.sqlite3'))
    return DatabasesResponse(databases=names)


@router.get('/categories-runs', response_model=CategoriesRunsResponse)
async def list_categories_runs() -> CategoriesRunsResponse:
    """List timestamped category-collection runs under saved_data/categories/."""
    cfg = get_config()
    cfg.CATEGORIES_DIR.mkdir(parents=True, exist_ok=True)
    runs = sorted((p.name for p in cfg.CATEGORIES_DIR.iterdir() if p.is_dir()), reverse=True)
    return CategoriesRunsResponse(runs=runs)


@router.post('/tasks/collect-categories', response_model=JobCreated)
async def start_collect_categories(request: Request, body: CollectCategoriesRequest) -> JobCreated:
    async def work(handle):
        handle.log(f'Starting categories collection (concurrency={body.concurrency})')
        await run_rustore_tasks(concurrency=body.concurrency)
        handle.log('Done.')

    job = _jobs(request).submit('collect-categories', work)
    return JobCreated(job_id=job.id, kind=job.kind)


@router.post('/tasks/collect-apps', response_model=JobCreated)
async def start_collect_apps(request: Request, body: CollectAppsRequest) -> JobCreated:
    async def work(handle):
        handle.log(f'Collecting apps into db={body.db_name} folder={body.folder_name or "<latest>"}')
        await run_rustore_app_info_tasks(
            db_name=body.db_name,
            folder_name=body.folder_name,
            concurrency=body.concurrency,
        )
        handle.log('Done.')

    job = _jobs(request).submit('collect-apps', work)
    return JobCreated(job_id=job.id, kind=job.kind)


@router.post('/tasks/index', response_model=JobCreated)
async def start_index(request: Request, body: IndexRequest) -> JobCreated:
    async def work(handle):
        handle.log(f'Indexing db={body.db_name} batch_size={body.batch_size}')
        await run_index_task(
            db_name=body.db_name,
            batch_size=body.batch_size,
            concurrency=body.concurrency,
        )
        handle.log('Done.')

    job = _jobs(request).submit('index', work)
    return JobCreated(job_id=job.id, kind=job.kind)


@router.get('/tasks/{job_id}', response_model=JobSnapshot)
async def get_task(request: Request, job_id: str) -> JobSnapshot:
    job = _jobs(request).get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail='Job not found')
    return JobSnapshot(**job.snapshot())


@router.get('/tasks/{job_id}/events')
async def task_events(request: Request, job_id: str) -> StreamingResponse:
    mgr = _jobs(request)
    if mgr.get(job_id) is None:
        raise HTTPException(status_code=404, detail='Job not found')
    return StreamingResponse(
        mgr.sse_stream(job_id),
        media_type='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'},
    )


@router.post('/tasks/{job_id}/cancel')
async def cancel_task(request: Request, job_id: str) -> dict:
    ok = _jobs(request).cancel(job_id)
    if not ok:
        raise HTTPException(status_code=404, detail='Job not found or already finished')
    return {'cancelled': True}


@router.post('/rag/query', response_model=RAGQueryResponse)
async def rag_query(request: Request, body: RAGQueryRequest) -> RAGQueryResponse:
    """Run the RAG pipeline against the selected DB."""
    service: RAGService = await request.app.state.get_rag_service(body.db_name)
    response = await service.answer(body.query, top_k=body.top_k)
    return RAGQueryResponse(
        answer=response.answer,
        filters=AppliedFilters(**asdict(response.filters)),
        sources=[
            SourceApp(
                app_id=src.app_id,
                name=src.name,
                url=src.url,
                rating=src.rating,
                downloads=src.downloads,
                categories=src.categories,
                distance=src.distance,
            )
            for src in response.sources
        ],
    )
