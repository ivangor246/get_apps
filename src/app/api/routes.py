from fastapi import APIRouter, Request

from app.services import RAGService

from .schemas import AppliedFilters, RAGQueryRequest, RAGQueryResponse, SourceApp

router = APIRouter()


@router.get('/health')
async def health() -> dict:
    """Liveness probe."""
    return {'status': 'ok'}


@router.post('/rag/query', response_model=RAGQueryResponse)
async def rag_query(request: Request, body: RAGQueryRequest) -> RAGQueryResponse:
    """Run the RAG pipeline for the given natural-language query."""
    service: RAGService = request.app.state.rag_service
    response = await service.answer(body.query, top_k=body.top_k)
    return RAGQueryResponse(
        answer=response.answer,
        filters=AppliedFilters(
            min_downloads=response.filters.min_downloads,
            max_downloads=response.filters.max_downloads,
            min_rating=response.filters.min_rating,
            categories_any=response.filters.categories_any,
            above_median_downloads=response.filters.above_median_downloads,
        ),
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
