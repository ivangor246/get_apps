from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Request

from app.core.exceptions import EmbeddingModelMissingError
from app.services import RAGService

from ..schemas.rag import AppliedFilters, RAGQueryRequest, RAGQueryResponse, SourceApp

router = APIRouter()


@router.post('/rag/query', response_model=RAGQueryResponse)
async def rag_query(request: Request, body: RAGQueryRequest) -> RAGQueryResponse:
    """Run the RAG pipeline against the selected DB."""
    service: RAGService = await request.app.state.get_rag_service(body.db_name)
    try:
        response = await service.answer(body.query, top_k=body.top_k)
    except EmbeddingModelMissingError as err:
        raise HTTPException(status_code=409, detail=str(err)) from err
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
