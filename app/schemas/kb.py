"""Knowledge base article Pydantic schemas — API-facing."""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class KBCategory(str, Enum):
    """Knowledge base categories (matches frontend)."""

    BILLING = "Billing"
    TECHNICAL = "Technical"
    ACCOUNT = "Account"
    FEATURES = "Features"
    FEATURE_REQUEST = "Feature Request"
    SHIPPING = "Shipping"
    SECURITY = "Security"


class KBStatus(str, Enum):
    """Indexing / publication status (matches frontend)."""

    INDEXED = "indexed"
    PROCESSING = "processing"
    FAILED = "failed"
    DRAFT = "draft"
    ARCHIVED = "archived"


class KBArticleCreateRequest(BaseModel):
    """API request body for creating a knowledge base article."""

    model_config = ConfigDict(populate_by_name=True)

    title: str = Field(..., min_length=1, max_length=500)
    slug: str | None = Field(default=None, min_length=1, max_length=500)
    category: KBCategory
    tags: list[str] = Field(default_factory=list)
    content: str = Field(..., min_length=1)
    summary: str = ""
    status: KBStatus = KBStatus.DRAFT


class KBArticleUpdateRequest(BaseModel):
    """API request body for updating a knowledge base article."""

    model_config = ConfigDict(populate_by_name=True)

    title: str | None = Field(default=None, min_length=1, max_length=500)
    slug: str | None = Field(default=None, min_length=1, max_length=500)
    category: KBCategory | None = None
    tags: list[str] | None = None
    content: str | None = Field(default=None, min_length=1)
    summary: str | None = None
    status: KBStatus | None = None
