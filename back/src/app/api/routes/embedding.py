from fastapi import APIRouter, HTTPException, Request

from ..deps import get_embedder, get_jobs
from ..schemas.tasks import JobCreated

router = APIRouter()


@router.post('/embedding/model/download', response_model=JobCreated)
async def download_embedding_model(request: Request) -> JobCreated:
    """Download the configured embedding model into the local cache as a background job."""
    embedder = get_embedder(request)
    if embedder.downloading:
        raise HTTPException(status_code=409, detail='Embedding model download is already in progress')

    async def work(handle):
        handle.log(f'Downloading embedding model {embedder.model_name}')
        await embedder.download()
        handle.log('Done.')

    job = get_jobs(request).submit('download-embedding-model', work)
    return JobCreated(job_id=job.id, kind=job.kind)
