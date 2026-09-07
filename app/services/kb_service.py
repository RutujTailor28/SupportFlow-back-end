"""Knowledge base service — article CRUD (no RAG yet)."""

from __future__ import annotations

import re
from typing import Any
from uuid import UUID

from app.core.exceptions import DatabaseError, NotFoundError
from app.schemas.kb import KBArticleCreateRequest, KBArticleUpdateRequest
from app.schemas.mappers import map_kb_article


def _slugify(title: str) -> str:
    """Generate a URL-safe slug from a title."""
    slug = title.strip().lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "-", slug)
    return slug.strip("-") or "article"


class KnowledgeBaseService:
    """Service layer for knowledge base article CRUD."""

    def __init__(self, db: Any) -> None:
        self.db = db

    def _ensure_unique_slug(self, slug: str, exclude_id: str | None = None) -> str:
        base = slug
        candidate = base
        counter = 2
        while True:
            query = self.db.table("kb_articles").select("id").eq("slug", candidate).limit(1)
            response = query.execute()
            if not response.data:
                return candidate
            if exclude_id and response.data[0]["id"] == exclude_id:
                return candidate
            candidate = f"{base}-{counter}"
            counter += 1

    def list_articles(
        self,
        *,
        category: str | None = None,
        status: str | None = None,
        search: str | None = None,
    ) -> list[dict[str, Any]]:
        """List knowledge base articles with optional filters."""
        query = self.db.table("kb_articles").select("*").order("updated_at", desc=True)

        if category:
            query = query.eq("category", category)
        if status:
            query = query.eq("status", status)
        if search:
            term = search.strip()
            query = query.or_(
                f"title.ilike.%{term}%,summary.ilike.%{term}%,content.ilike.%{term}%"
            )

        response = query.execute()
        return [map_kb_article(row) for row in (response.data or [])]

    def get_article(self, article_id: UUID) -> dict[str, Any]:
        """Fetch a single knowledge base article."""
        response = (
            self.db.table("kb_articles")
            .select("*")
            .eq("id", str(article_id))
            .limit(1)
            .execute()
        )
        if not response.data:
            raise NotFoundError("Knowledge base article not found", code="KB_ARTICLE_NOT_FOUND")
        return map_kb_article(response.data[0])

    def create_article(self, payload: KBArticleCreateRequest) -> dict[str, Any]:
        """Create a new knowledge base article."""
        slug = payload.slug.strip() if payload.slug else _slugify(payload.title)
        slug = self._ensure_unique_slug(slug)

        insert_payload = {
            "title": payload.title.strip(),
            "slug": slug,
            "category": payload.category.value,
            "tags": payload.tags,
            "content": payload.content.strip(),
            "summary": payload.summary.strip(),
            "status": payload.status.value,
        }
        response = self.db.table("kb_articles").insert(insert_payload).execute()
        if not response.data:
            raise DatabaseError("Failed to create knowledge base article")
        return map_kb_article(response.data[0])

    def update_article(
        self,
        article_id: UUID,
        payload: KBArticleUpdateRequest,
    ) -> dict[str, Any]:
        """Partially update a knowledge base article."""
        existing = self.get_article(article_id)
        update_data = payload.model_dump(exclude_unset=True, by_alias=False)

        db_update: dict[str, Any] = {}
        if "title" in update_data and update_data["title"] is not None:
            db_update["title"] = update_data["title"].strip()
        if "slug" in update_data and update_data["slug"] is not None:
            db_update["slug"] = self._ensure_unique_slug(
                update_data["slug"].strip(),
                exclude_id=str(existing["id"]),
            )
        if "category" in update_data and update_data["category"] is not None:
            db_update["category"] = update_data["category"].value
        if "tags" in update_data and update_data["tags"] is not None:
            db_update["tags"] = update_data["tags"]
        if "content" in update_data and update_data["content"] is not None:
            db_update["content"] = update_data["content"].strip()
        if "summary" in update_data and update_data["summary"] is not None:
            db_update["summary"] = update_data["summary"].strip()
        if "status" in update_data and update_data["status"] is not None:
            db_update["status"] = update_data["status"].value

        if not db_update:
            return existing

        response = (
            self.db.table("kb_articles")
            .update(db_update)
            .eq("id", str(article_id))
            .execute()
        )
        if not response.data:
            raise DatabaseError("Failed to update knowledge base article")
        return map_kb_article(response.data[0])

    def delete_article(self, article_id: UUID) -> None:
        """Delete a knowledge base article."""
        self.get_article(article_id)
        self.db.table("kb_articles").delete().eq("id", str(article_id)).execute()
