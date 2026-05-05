from dataclasses import asdict

from fastapi import APIRouter, Query, Request

from app.schemas import (
    AppliedFilters,
    RAGQueryRequest,
    RAGQueryResponse,
    SourceApp,
)
from app.services import RAGService

router = APIRouter(prefix='/rag', tags=['rag'])


@router.post('/query', response_model=RAGQueryResponse)
async def rag_query(
    request: Request,
    body: RAGQueryRequest,
    top_k: int | None = Query(default=None, ge=1, le=100),
    candidate_k: int | None = Query(default=None, ge=1, le=10000),
    llm_model: str | None = Query(default=None, min_length=1),
    ollama_timeout: float | None = Query(default=None, gt=0),
    ollama_context_size: int | None = Query(default=None, ge=1),
) -> RAGQueryResponse:
    """Run the RAG pipeline against the selected DB."""
    service: RAGService = await request.app.state.get_rag_service(body.db_name)
    response = await service.answer(
        body.query,
        top_k=top_k,
        candidate_k=candidate_k,
        llm_model=llm_model,
        ollama_timeout=ollama_timeout,
        ollama_context_size=ollama_context_size,
    )
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
        intent=response.intent,
        language=response.language,
        iterations=response.iterations,
    )
