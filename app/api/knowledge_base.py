"""Knowledge base API router — article CRUD (no RAG yet)."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse

from app.core.deps import get_db
from app.schemas.kb import KBArticleCreateRequest, KBArticleUpdateRequest
from app.services.kb_service import KnowledgeBaseService

router = APIRouter(prefix="/kb-articles", tags=["knowledge-base"])


def get_kb_service(db=Depends(get_db)) -> KnowledgeBaseService:  # noqa: ANN001
    """Provide a knowledge base service bound to the Supabase admin client."""
    return KnowledgeBaseService(db)


@router.get("")
async def list_kb_articles(
    category: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None),
    service: KnowledgeBaseService = Depends(get_kb_service),
) -> JSONResponse:
    """List knowledge base articles with optional filters."""
    articles = service.list_articles(
        category=category,
        status=status_filter,
        search=search,
    )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "count": len(articles),
            "data": articles,
        },
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_kb_article(
    payload: KBArticleCreateRequest,
    service: KnowledgeBaseService = Depends(get_kb_service),
) -> JSONResponse:
    """Create a new knowledge base article."""
    data = service.create_article(payload)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "success": True,
            "message": "Knowledge base article created successfully",
            "data": data,
        },
    )


@router.get("/{article_id}")
async def get_kb_article(
    article_id: UUID,
    service: KnowledgeBaseService = Depends(get_kb_service),
) -> JSONResponse:
    """Get a single knowledge base article."""
    data = service.get_article(article_id)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "data": data,
        },
    )


@router.put("/{article_id}")
async def update_kb_article(
    article_id: UUID,
    payload: KBArticleUpdateRequest,
    service: KnowledgeBaseService = Depends(get_kb_service),
) -> JSONResponse:
    """Update a knowledge base article."""
    data = service.update_article(article_id, payload)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "Knowledge base article updated successfully",
            "data": data,
        },
    )


@router.delete("/{article_id}")
async def delete_kb_article(
    article_id: UUID,
    service: KnowledgeBaseService = Depends(get_kb_service),
) -> JSONResponse:
    """Delete a knowledge base article."""
    service.delete_article(article_id)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "Knowledge base article deleted successfully",
        },
    )
