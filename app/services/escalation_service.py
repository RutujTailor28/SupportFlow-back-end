"""Escalation service — detect, create, list, and acknowledge ticket escalations."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from app.core.exceptions import AppError, DatabaseError, NotFoundError, TicketNotFoundError
from app.schemas.escalation import EscalationAcknowledgeRequest, EscalationCreateRequest, EscalationReason
from app.schemas.mappers import map_escalation, map_escalation_summary


class EscalationService:
    """Service layer for escalation detection and record management."""

    DETECTION_RULES: dict[EscalationReason, list[str]] = {
        EscalationReason.CHURN_RISK: [
            r"cancel\s+(my\s+)?(account|subscription)",
            r"switching\s+to",
            r"competitor",
            r"leave\s+your\s+service",
        ],
        EscalationReason.LEGAL_LANGUAGE: [
            r"lawyer",
            r"legal\s+action",
            r"sue",
            r"attorney",
            r"regulator",
        ],
        EscalationReason.SLA_RISK: [
            r"still\s+waiting",
            r"no\s+response",
            r"unacceptable\s+delay",
            r"breach",
        ],
        EscalationReason.REPEAT_CONTACT: [
            r"again",
            r"still\s+not\s+resolved",
            r"third\s+time",
            r"follow\s+up",
        ],
        EscalationReason.EXECUTIVE_ESCALATION: [
            r"ceo",
            r"executive",
            r"manager",
            r"escalate\s+to\s+leadership",
        ],
        EscalationReason.SECURITY_THREAT: [
            r"\bhacked\b",
            r"unauthorized\s+access",
            r"data\s+breach",
            r"security\s+incident",
        ],
    }

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

    def _get_ticket_text(self, ticket_id: UUID) -> str:
        ticket = self._get_ticket(ticket_id)
        messages_response = (
            self.db.table("ticket_messages")
            .select("body")
            .eq("ticket_id", str(ticket_id))
            .order("created_at", desc=False)
            .execute()
        )
        parts = [ticket.get("subject", ""), ticket.get("body", "")]
        parts.extend(message["body"] for message in (messages_response.data or []))
        return "\n".join(part for part in parts if part).lower()

    def _escalation_exists(self, ticket_id: UUID, reason: str) -> bool:
        response = (
            self.db.table("ticket_escalations")
            .select("id")
            .eq("ticket_id", str(ticket_id))
            .eq("reason", reason)
            .limit(1)
            .execute()
        )
        return bool(response.data)

    def _insert_escalation(
        self,
        ticket_id: UUID,
        *,
        reason: str,
        trigger_phrases: list[str],
        source: str,
        notes: str | None = None,
    ) -> dict[str, Any]:
        payload = {
            "ticket_id": str(ticket_id),
            "reason": reason,
            "trigger_phrases": trigger_phrases,
            "source": source,
            "notes": notes,
        }
        response = self.db.table("ticket_escalations").insert(payload).execute()
        if not response.data:
            raise DatabaseError("Failed to create escalation")
        return map_escalation(response.data[0])

    def get_escalations(self, ticket_id: UUID) -> list[dict[str, Any]]:
        """List all escalation records for a ticket."""
        self._get_ticket(ticket_id)
        response = (
            self.db.table("ticket_escalations")
            .select("*")
            .eq("ticket_id", str(ticket_id))
            .order("created_at", desc=False)
            .execute()
        )
        return [map_escalation(row) for row in (response.data or [])]

    def get_escalation_summary(self, ticket_id: UUID) -> dict[str, Any]:
        """Return frontend-compatible escalation summary for a ticket."""
        return map_escalation_summary(self.get_escalations(ticket_id))

    def create_escalation(
        self,
        ticket_id: UUID,
        payload: EscalationCreateRequest,
    ) -> dict[str, Any]:
        """Manually create an escalation record for a ticket."""
        self._get_ticket(ticket_id)
        if self._escalation_exists(ticket_id, payload.reason.value):
            raise AppError(
                f"Escalation already exists for reason: {payload.reason.value}",
                code="ESCALATION_ALREADY_EXISTS",
                status_code=409,
            )
        return self._insert_escalation(
            ticket_id,
            reason=payload.reason.value,
            trigger_phrases=payload.trigger_phrases,
            source=payload.source.value,
            notes=payload.notes,
        )

    def acknowledge_escalation(
        self,
        ticket_id: UUID,
        escalation_id: UUID,
        payload: EscalationAcknowledgeRequest,
    ) -> dict[str, Any]:
        """Acknowledge or update an escalation record."""
        self._get_ticket(ticket_id)
        response = (
            self.db.table("ticket_escalations")
            .select("*")
            .eq("id", str(escalation_id))
            .eq("ticket_id", str(ticket_id))
            .limit(1)
            .execute()
        )
        if not response.data:
            raise NotFoundError("Escalation not found", code="ESCALATION_NOT_FOUND")

        update_data: dict[str, Any] = {"acknowledged": payload.acknowledged}
        if payload.notes is not None:
            update_data["notes"] = payload.notes
        if payload.acknowledged:
            update_data["acknowledged_at"] = datetime.now(UTC).isoformat()
        else:
            update_data["acknowledged_at"] = None

        updated = (
            self.db.table("ticket_escalations")
            .update(update_data)
            .eq("id", str(escalation_id))
            .execute()
        )
        if not updated.data:
            raise DatabaseError("Failed to update escalation")
        return map_escalation(updated.data[0])

    def detect_escalations(self, ticket_id: UUID) -> list[dict[str, Any]]:
        """Run keyword-based escalation detection on ticket content (no AI API)."""
        text = self._get_ticket_text(ticket_id)
        created: list[dict[str, Any]] = []

        for reason, patterns in self.DETECTION_RULES.items():
            if self._escalation_exists(ticket_id, reason.value):
                continue

            matched_phrases: list[str] = []
            for pattern in patterns:
                for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                    matched_phrases.append(match.group(0).strip())

            if matched_phrases:
                created.append(
                    self._insert_escalation(
                        ticket_id,
                        reason=reason.value,
                        trigger_phrases=list(dict.fromkeys(matched_phrases)),
                        source="detection",
                        notes="Auto-detected from ticket content",
                    )
                )

        return created

    def detect_churn_risk(self, ticket_id: UUID) -> dict[str, Any] | None:
        """Detect churn-risk language and create an escalation if found."""
        return self._detect_single(ticket_id, EscalationReason.CHURN_RISK)

    def detect_legal_language(self, ticket_id: UUID) -> dict[str, Any] | None:
        """Detect legal language and create an escalation if found."""
        return self._detect_single(ticket_id, EscalationReason.LEGAL_LANGUAGE)

    def detect_repeat_contacts(self, ticket_id: UUID) -> dict[str, Any] | None:
        """Detect repeat-contact language and create an escalation if found."""
        return self._detect_single(ticket_id, EscalationReason.REPEAT_CONTACT)

    def detect_sla_risk(self, ticket_id: UUID) -> dict[str, Any] | None:
        """Detect SLA-risk language and create an escalation if found."""
        return self._detect_single(ticket_id, EscalationReason.SLA_RISK)

    def _detect_single(self, ticket_id: UUID, reason: EscalationReason) -> dict[str, Any] | None:
        if self._escalation_exists(ticket_id, reason.value):
            return None

        text = self._get_ticket_text(ticket_id)
        matched_phrases: list[str] = []
        for pattern in self.DETECTION_RULES[reason]:
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                matched_phrases.append(match.group(0).strip())

        if not matched_phrases:
            return None

        return self._insert_escalation(
            ticket_id,
            reason=reason.value,
            trigger_phrases=list(dict.fromkeys(matched_phrases)),
            source="detection",
            notes=f"Auto-detected: {reason.value}",
        )
