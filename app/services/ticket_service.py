"""Ticket service — create, list, retrieve, and update support tickets."""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID

from app.core.exceptions import DatabaseError, TicketNotFoundError
from app.schemas.mappers import map_ticket_detail, map_ticket_summary
from app.schemas.ticket import TicketCreateRequest, TicketUpdateRequest
from app.services.classification_service import ClassificationService
from app.services.escalation_service import EscalationService


class TicketService:
    """Service layer for ticket CRUD and lifecycle operations."""

    def __init__(self, db: Any) -> None:
        self.db = db

    def _get_customer_by_email(self, email: str) -> dict[str, Any] | None:
        response = (
            self.db.table("customers")
            .select("*")
            .eq("email", email.lower())
            .limit(1)
            .execute()
        )
        if response.data:
            return response.data[0]
        return None

    def _get_customer_by_id(self, customer_id: str) -> dict[str, Any] | None:
        response = (
            self.db.table("customers")
            .select("*")
            .eq("id", customer_id)
            .limit(1)
            .execute()
        )
        if response.data:
            return response.data[0]
        return None

    def _find_or_create_customer(self, name: str, email: str) -> dict[str, Any]:
        normalized_email = email.strip().lower()
        existing = self._get_customer_by_email(normalized_email)
        if existing:
            return existing

        payload = {
            "name": name.strip(),
            "email": normalized_email,
            "joined_date": date.today().isoformat(),
        }
        response = self.db.table("customers").insert(payload).execute()
        if not response.data:
            raise DatabaseError("Failed to create customer")
        return response.data[0]

    def create_ticket(self, payload: TicketCreateRequest) -> dict[str, Any]:
        """Create or find customer, create ticket, and store the initial message."""
        customer = self._find_or_create_customer(payload.customer_name, payload.customer_email)

        ticket_payload = {
            "customer_id": customer["id"],
            "subject": payload.subject.strip(),
            "body": payload.body.strip(),
            "channel": payload.channel.value,
            "status": "new",
            "priority": "normal",
            "ticket_number": "",
        }
        ticket_response = self.db.table("tickets").insert(ticket_payload).execute()
        if not ticket_response.data:
            raise DatabaseError("Failed to create ticket")
        ticket = ticket_response.data[0]

        message_payload = {
            "ticket_id": ticket["id"],
            "sender_type": "customer",
            "sender_name": customer["name"],
            "body": payload.body.strip(),
            "direction": "in",
        }
        self.db.table("ticket_messages").insert(message_payload).execute()

        return map_ticket_summary(ticket, customer)

    def get_tickets(
        self,
        *,
        status: str | None = None,
        category: str | None = None,
        urgency: str | None = None,
        sentiment: str | None = None,
        assigned_team: str | None = None,
        search: str | None = None,
    ) -> list[dict[str, Any]]:
        """List tickets with optional filters."""
        query = self.db.table("tickets").select("*").order("created_at", desc=True)

        if status:
            query = query.eq("status", status)
        if category:
            query = query.eq("category", category)
        if urgency:
            query = query.eq("priority", urgency)
        if sentiment:
            query = query.eq("sentiment", sentiment)
        if assigned_team:
            query = query.eq("assigned_team", assigned_team)
        if search:
            term = search.strip()
            query = query.or_(f"subject.ilike.%{term}%,body.ilike.%{term}%")

        response = query.execute()
        tickets = response.data or []

        results: list[dict[str, Any]] = []
        for ticket in tickets:
            customer = self._get_customer_by_id(ticket["customer_id"])
            if customer:
                results.append(map_ticket_summary(ticket, customer))
        return results

    def get_ticket(self, ticket_id: UUID) -> dict[str, Any]:
        """Fetch a single ticket with customer and messages."""
        response = (
            self.db.table("tickets")
            .select("*")
            .eq("id", str(ticket_id))
            .limit(1)
            .execute()
        )
        if not response.data:
            raise TicketNotFoundError(str(ticket_id))

        ticket = response.data[0]
        customer = self._get_customer_by_id(ticket["customer_id"])
        if not customer:
            raise DatabaseError("Ticket customer record is missing")

        messages_response = (
            self.db.table("ticket_messages")
            .select("*")
            .eq("ticket_id", str(ticket_id))
            .order("created_at", desc=False)
            .execute()
        )
        messages = messages_response.data or []

        classification_service = ClassificationService(self.db)
        classification = classification_service.get_classification(ticket_id)

        escalation_service = EscalationService(self.db)
        escalations = escalation_service.get_escalations(ticket_id)

        return map_ticket_detail(ticket, customer, messages, classification, escalations)

    def update_ticket(self, ticket_id: UUID, payload: TicketUpdateRequest) -> dict[str, Any]:
        """Partially update a ticket."""
        existing_response = (
            self.db.table("tickets")
            .select("*")
            .eq("id", str(ticket_id))
            .limit(1)
            .execute()
        )
        if not existing_response.data:
            raise TicketNotFoundError(str(ticket_id))

        update_data = payload.model_dump(exclude_unset=True, by_alias=False)
        db_update: dict[str, Any] = {}

        if "status" in update_data and update_data["status"] is not None:
            db_update["status"] = update_data["status"].value
            if update_data["status"].value == "resolved":
                db_update["resolved_at"] = datetime.now(UTC).isoformat()
        if "priority" in update_data and update_data["priority"] is not None:
            db_update["priority"] = update_data["priority"].value
        if "assigned_team" in update_data:
            db_update["assigned_team"] = update_data["assigned_team"]
        if "assigned_agent_id" in update_data:
            db_update["assigned_agent_id"] = (
                str(update_data["assigned_agent_id"])
                if update_data["assigned_agent_id"] is not None
                else None
            )

        if not db_update:
            ticket = existing_response.data[0]
            customer = self._get_customer_by_id(ticket["customer_id"])
            if not customer:
                raise DatabaseError("Ticket customer record is missing")
            return map_ticket_summary(ticket, customer)

        response = (
            self.db.table("tickets")
            .update(db_update)
            .eq("id", str(ticket_id))
            .execute()
        )
        if not response.data:
            raise DatabaseError("Failed to update ticket")

        ticket = response.data[0]
        customer = self._get_customer_by_id(ticket["customer_id"])
        if not customer:
            raise DatabaseError("Ticket customer record is missing")
        return map_ticket_summary(ticket, customer)
