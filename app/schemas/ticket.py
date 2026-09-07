"""Ticket-related Pydantic schemas — internal and API-facing."""

from datetime import date, datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TicketStatus(str, Enum):
    """Supported ticket lifecycle statuses (matches frontend)."""

    NEW = "new"
    OPEN = "open"
    PENDING = "pending"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, Enum):
    """Supported ticket priority levels (matches frontend)."""

    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class TicketChannel(str, Enum):
    """Supported ticket intake channels."""

    WEB = "web"
    EMAIL = "email"
    CHAT = "chat"
    PHONE = "phone"
    API = "api"


class TicketCreateRequest(BaseModel):
    """API request body for creating a ticket (camelCase from frontend)."""

    model_config = ConfigDict(populate_by_name=True)

    customer_name: str = Field(..., alias="customerName", min_length=1, max_length=255)
    customer_email: str = Field(..., alias="customerEmail", min_length=3, max_length=320)
    subject: str = Field(..., min_length=1, max_length=500)
    body: str = Field(..., min_length=1)
    channel: TicketChannel = TicketChannel.WEB


class TicketUpdateRequest(BaseModel):
    """API request body for partially updating a ticket."""

    model_config = ConfigDict(populate_by_name=True)

    status: TicketStatus | None = None
    priority: TicketPriority | None = None
    assigned_team: str | None = Field(default=None, alias="assignedTeam")
    assigned_agent_id: UUID | None = Field(default=None, alias="assignedAgentId")


class CustomerSummary(BaseModel):
    """Customer fields returned with ticket responses."""

    model_config = ConfigDict(populate_by_name=True)

    id: UUID
    name: str
    email: str
    avatar: str | None = Field(default=None, alias="avatar")
    company: str | None = None
    plan: str = "Free"
    is_vip: bool = Field(default=False, alias="isVip")
    joined_date: date | None = Field(default=None, alias="joinedDate")


class MessageResponse(BaseModel):
    """Message returned with ticket detail."""

    model_config = ConfigDict(populate_by_name=True)

    id: UUID
    sender_type: str = Field(alias="senderType")
    sender_name: str = Field(alias="senderName")
    sender_avatar: str | None = Field(default=None, alias="senderAvatar")
    content: str
    timestamp: datetime
    direction: str
    is_ai_generated: bool = Field(default=False, alias="isAiGenerated")
    ai_confidence: float | None = Field(default=None, alias="aiConfidence")


class TicketSummaryResponse(BaseModel):
    """Ticket summary for list and create responses."""

    model_config = ConfigDict(populate_by_name=True)

    id: UUID
    ticket_number: str = Field(alias="ticketNumber")
    customer_name: str = Field(alias="customerName")
    customer_email: str = Field(alias="customerEmail")
    subject: str
    body: str
    status: TicketStatus
    priority: TicketPriority
    channel: TicketChannel
    category: str | None = None
    sentiment: str | None = None
    assigned_team: str | None = Field(default=None, alias="assignedTeam")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime | None = Field(default=None, alias="updatedAt")
    sla_due_at: datetime | None = Field(default=None, alias="slaDueAt")


class TicketDetailResponse(BaseModel):
    """Full ticket detail with customer and messages."""

    model_config = ConfigDict(populate_by_name=True)

    ticket: dict[str, Any]
    customer: CustomerSummary
    messages: list[MessageResponse]
