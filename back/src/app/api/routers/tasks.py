from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.core.jobs import JobManager
from app.schemas import (
    CollectAppsRequest,
    CollectCategoriesRequest,
    IndexRequest,
    JobCreated,
    JobSnapshot,
)
from app.tasks.index import run_index_task
from app.tasks.rustore import run_rustore_tasks
from app.tasks.rustore_app_info import run_rustore_app_info_tasks

router = APIRouter(prefix='/tasks', tags=['tasks'])


def _jobs(request: Request) -> JobManager:
    return request.app.state.jobs


@router.post('/collect-categories', response_model=JobCreated)
async def start_collect_categories(request: Request, body: CollectCategoriesRequest) -> JobCreated:
    async def work(handle):
        handle.log(f'Starting categories collection (concurrency={body.concurrency})')
        await run_rustore_tasks(concurrency=body.concurrency)
        handle.log('Done.')

    job = _jobs(request).submit('collect-categories', work)
    return JobCreated(job_id=job.id, kind=job.kind)


@router.post('/collect-apps', response_model=JobCreated)
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


@router.post('/index', response_model=JobCreated)
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


@router.get('/{job_id}', response_model=JobSnapshot)
async def get_task(request: Request, job_id: str) -> JobSnapshot:
    job = _jobs(request).get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail='Job not found')
    return JobSnapshot(**job.snapshot())


@router.get('/{job_id}/events')
async def task_events(request: Request, job_id: str) -> StreamingResponse:
    mgr = _jobs(request)
    if mgr.get(job_id) is None:
        raise HTTPException(status_code=404, detail='Job not found')
    return StreamingResponse(
        mgr.sse_stream(job_id),
        media_type='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'},
    )


@router.post('/{job_id}/cancel')
async def cancel_task(request: Request, job_id: str) -> dict:
    ok = _jobs(request).cancel(job_id)
    if not ok:
        raise HTTPException(status_code=404, detail='Job not found or already finished')
    return {'cancelled': True}
