"""Classification-related Pydantic schemas — API-facing."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ClassificationUpdateRequest(BaseModel):
    """API request body for creating or correcting a ticket classification."""

    model_config = ConfigDict(populate_by_name=True)

    category: str | None = None
    subcategory: str | None = None
    urgency: str | None = None
    sentiment: str | None = None
    language: str | None = None
    intent_summary: str | None = Field(default=None, alias="intentSummary")
    entities: dict[str, Any] | list[Any] | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    notes: str | None = None
    human_corrected: bool | None = Field(default=None, alias="humanCorrected")
