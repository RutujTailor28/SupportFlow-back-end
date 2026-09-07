"""Message-related Pydantic schemas."""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class MessageDirection(str, Enum):
    """Message direction relative to the support team."""

    IN = "in"
    OUT = "out"


class MessageSenderType(str, Enum):
    """Who sent the message (matches frontend)."""

    CUSTOMER = "customer"
    AGENT = "agent"
    SYSTEM = "system"
    AI = "ai"


class MessageCreateRequest(BaseModel):
    """API request body for creating a ticket message."""

    model_config = ConfigDict(populate_by_name=True)

    direction: MessageDirection
    author: str = Field(..., min_length=1, max_length=255)
    body: str = Field(..., min_length=1)
    sender_type: MessageSenderType | None = Field(default=None, alias="senderType")
    sender_avatar: str | None = Field(default=None, alias="senderAvatar")
    is_ai_generated: bool = Field(default=False, alias="isAiGenerated")
    ai_confidence: float | None = Field(default=None, alias="aiConfidence", ge=0.0, le=1.0)
