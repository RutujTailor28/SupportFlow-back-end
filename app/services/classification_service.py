"""Classification service — create, correct, and retrieve ticket classifications."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from app.core.exceptions import AppError, DatabaseError, TicketNotFoundError
from app.schemas.classification import ClassificationUpdateRequest
from app.schemas.mappers import map_classification


class ClassificationService:
    """Service layer for ticket classification and human corrections."""

    CLASSIFICATION_FIELDS = (
        "category",
        "subcategory",
        "urgency",
        "sentiment",
        "language",
        "intent_summary",
        "entities",
        "confidence",
    )

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

    def _get_classification(self, ticket_id: UUID) -> dict[str, Any] | None:
        response = (
            self.db.table("ticket_classifications")
            .select("*")
            .eq("ticket_id", str(ticket_id))
            .limit(1)
            .execute()
        )
        if response.data:
            return response.data[0]
        return None

    def _get_latest_correction(self, ticket_id: UUID) -> dict[str, Any] | None:
        response = (
            self.db.table("classification_corrections")
            .select("*")
            .eq("ticket_id", str(ticket_id))
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if response.data:
            return response.data[0]
        return None

    def _extract_classification_fields(self, payload: ClassificationUpdateRequest) -> dict[str, Any]:
        data = payload.model_dump(exclude_unset=True, by_alias=False)
        return {
            key: data[key]
            for key in self.CLASSIFICATION_FIELDS
            if key in data and data[key] is not None
        }

    def _sync_ticket_from_effective(
        self,
        ticket_id: UUID,
        classification: dict[str, Any],
        correction: dict[str, Any] | None,
    ) -> None:
        """Denormalize effective classification fields onto the tickets row."""
        ticket_update: dict[str, Any] = {}

        category = correction.get("category") if correction else classification.get("category")
        sentiment = correction.get("sentiment") if correction else classification.get("sentiment")
        urgency = correction.get("urgency") if correction else classification.get("urgency")

        if category is not None:
            ticket_update["category"] = category
        if sentiment is not None:
            ticket_update["sentiment"] = sentiment
        if urgency is not None:
            ticket_update["priority"] = urgency

        if ticket_update:
            self.db.table("tickets").update(ticket_update).eq("id", str(ticket_id)).execute()

    def get_classification(self, ticket_id: UUID) -> dict[str, Any] | None:
        """Return effective classification for a ticket, if present."""
        classification = self._get_classification(ticket_id)
        if not classification:
            return None
        correction = self._get_latest_correction(ticket_id)
        return map_classification(classification, correction)

    def update_classification(
        self,
        ticket_id: UUID,
        payload: ClassificationUpdateRequest,
    ) -> dict[str, Any]:
        """Create an initial classification or record a human correction."""
        self._get_ticket(ticket_id)
        fields = self._extract_classification_fields(payload)
        if not fields:
            raise AppError(
                "At least one classification field must be provided",
                code="CLASSIFICATION_FIELDS_REQUIRED",
                status_code=422,
            )

        existing = self._get_classification(ticket_id)

        if existing is None:
            insert_payload = {
                "ticket_id": str(ticket_id),
                "source": "manual",
                **fields,
            }
            response = self.db.table("ticket_classifications").insert(insert_payload).execute()
            if not response.data:
                raise DatabaseError("Failed to create classification")
            classification = response.data[0]
            self._sync_ticket_from_effective(ticket_id, classification, None)
            return map_classification(classification)

        is_correction = payload.human_corrected is True or existing.get("source") == "ai"
        if is_correction:
            correction_payload = {
                "ticket_id": str(ticket_id),
                "classification_id": existing["id"],
                "notes": payload.notes,
                **fields,
            }
            correction_response = (
                self.db.table("classification_corrections").insert(correction_payload).execute()
            )
            if not correction_response.data:
                raise DatabaseError("Failed to record classification correction")

            flag_response = (
                self.db.table("ticket_classifications")
                .update({"human_corrected": True})
                .eq("id", existing["id"])
                .execute()
            )
            if not flag_response.data:
                raise DatabaseError("Failed to update classification correction flag")

            classification = flag_response.data[0]
            correction = correction_response.data[0]
            self._sync_ticket_from_effective(ticket_id, classification, correction)
            return map_classification(classification, correction)

        update_response = (
            self.db.table("ticket_classifications")
            .update(fields)
            .eq("id", existing["id"])
            .execute()
        )
        if not update_response.data:
            raise DatabaseError("Failed to update classification")
        classification = update_response.data[0]
        self._sync_ticket_from_effective(ticket_id, classification, None)
        return map_classification(classification)

    def create_ai_classification(
        self,
        ticket_id: UUID,
        fields: dict[str, Any],
    ) -> dict[str, Any]:
        """Create an AI classification without overwriting an existing record."""
        existing = self._get_classification(ticket_id)
        if existing:
            return map_classification(existing, self._get_latest_correction(ticket_id))

        insert_payload = {
            "ticket_id": str(ticket_id),
            "source": "ai",
            **fields,
        }
        response = self.db.table("ticket_classifications").insert(insert_payload).execute()
        if not response.data:
            raise DatabaseError("Failed to create AI classification")
        classification = response.data[0]
        self._sync_ticket_from_effective(ticket_id, classification, None)
        return map_classification(classification)
