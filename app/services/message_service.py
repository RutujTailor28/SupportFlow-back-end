"""Message service — create and list ticket conversation messages."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from app.core.exceptions import DatabaseError, TicketNotFoundError
from app.schemas.mappers import map_message
from app.schemas.message import MessageCreateRequest, MessageDirection, MessageSenderType


class MessageService:
    """Service layer for ticket message operations."""

    def __init__(self, db: Any) -> None:
        self.db = db

    def _get_ticket(self, ticket_id: UUID) -> dict[str, Any]:
        response = (
            self.db.table("tickets")
            .select("*")
            .eq("id", str(ticket_id))
            .limit(1)
            .execute()
        )
        if not response.data:
            raise TicketNotFoundError(str(ticket_id))
        return response.data[0]

    def _resolve_sender_type(self, payload: MessageCreateRequest) -> str:
        if payload.sender_type is not None:
            return payload.sender_type.value
        if payload.direction == MessageDirection.IN:
            return MessageSenderType.CUSTOMER.value
        return MessageSenderType.AGENT.value

    def create_message(self, ticket_id: UUID, payload: MessageCreateRequest) -> dict[str, Any]:
        """Add a message to a ticket and update first-response metadata when needed."""
        ticket = self._get_ticket(ticket_id)
        sender_type = self._resolve_sender_type(payload)

        message_payload = {
            "ticket_id": str(ticket_id),
            "sender_type": sender_type,
            "sender_name": payload.author.strip(),
            "sender_avatar": payload.sender_avatar,
            "body": payload.body.strip(),
            "direction": payload.direction.value,
            "is_ai_generated": payload.is_ai_generated,
            "ai_confidence": payload.ai_confidence,
        }

        response = self.db.table("ticket_messages").insert(message_payload).execute()
        if not response.data:
            raise DatabaseError("Failed to create message")
        message = response.data[0]

        ticket_update: dict[str, Any] = {}
        if payload.direction == MessageDirection.OUT and ticket.get("first_response_at") is None:
            ticket_update["first_response_at"] = datetime.now(UTC).isoformat()
        if ticket.get("status") == "new" and payload.direction == MessageDirection.OUT:
            ticket_update["status"] = "open"

        if ticket_update:
            self.db.table("tickets").update(ticket_update).eq("id", str(ticket_id)).execute()

        return map_message(message)

    def get_messages(self, ticket_id: UUID) -> list[dict[str, Any]]:
        """List all messages for a ticket in chronological order."""
        self._get_ticket(ticket_id)

        response = (
            self.db.table("ticket_messages")
            .select("*")
            .eq("ticket_id", str(ticket_id))
            .order("created_at", desc=False)
            .execute()
        )
        messages = response.data or []
        return [map_message(message) for message in messages]
