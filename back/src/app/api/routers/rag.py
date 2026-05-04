from dataclasses import asdict

from fastapi import APIRouter, Request

from app.schemas import (
    AppliedFilters,
    RAGQueryRequest,
    RAGQueryResponse,
    SourceApp,
)
from app.services import RAGService

router = APIRouter(prefix='/rag', tags=['rag'])


@router.post('/query', response_model=RAGQueryResponse)
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
        intent=response.intent,
        language=response.language,
        iterations=response.iterations,
    )
