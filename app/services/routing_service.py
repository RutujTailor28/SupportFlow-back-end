"""Routing service — CRUD and deterministic rule evaluation."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from app.core.exceptions import AppError, DatabaseError, NotFoundError, TicketNotFoundError
from app.schemas.mappers import map_routing_rule
from app.schemas.routing_rule import RoutingRuleCreateRequest, RoutingRuleUpdateRequest

PRIORITY_RANK = {
    "low": 1,
    "normal": 2,
    "high": 3,
    "critical": 4,
}


class RoutingService:
    """Service layer for routing rule management and evaluation."""

    def __init__(self, db: Any) -> None:
        self.db = db

    def _serialize_conditions(self, conditions: list[Any]) -> list[dict[str, Any]]:
        serialized: list[dict[str, Any]] = []
        for condition in conditions:
            data = condition.model_dump(by_alias=True)
            if not data.get("id"):
                data["id"] = f"cond-{uuid4()}"
            serialized.append(data)
        return serialized

    def _serialize_actions(self, actions: Any) -> dict[str, Any]:
        return actions.model_dump(by_alias=True, exclude_none=True)

    def list_rules(self) -> list[dict[str, Any]]:
        """List all routing rules ordered by rule_order."""
        response = (
            self.db.table("routing_rules")
            .select("*")
            .order("rule_order", desc=False)
            .execute()
        )
        return [map_routing_rule(row) for row in (response.data or [])]

    def get_rule(self, rule_id: UUID) -> dict[str, Any]:
        """Fetch a single routing rule."""
        response = (
            self.db.table("routing_rules")
            .select("*")
            .eq("id", str(rule_id))
            .limit(1)
            .execute()
        )
        if not response.data:
            raise NotFoundError("Routing rule not found", code="ROUTING_RULE_NOT_FOUND")
        return map_routing_rule(response.data[0])

    def create_rule(self, payload: RoutingRuleCreateRequest) -> dict[str, Any]:
        """Create a new routing rule."""
        insert_payload = {
            "name": payload.name.strip(),
            "description": payload.description.strip(),
            "rule_order": payload.order,
            "enabled": payload.enabled,
            "match_type": payload.match_type.value,
            "conditions": self._serialize_conditions(payload.conditions),
            "actions": self._serialize_actions(payload.actions),
        }
        response = self.db.table("routing_rules").insert(insert_payload).execute()
        if not response.data:
            raise DatabaseError("Failed to create routing rule")
        return map_routing_rule(response.data[0])

    def update_rule(self, rule_id: UUID, payload: RoutingRuleUpdateRequest) -> dict[str, Any]:
        """Update an existing routing rule."""
        self.get_rule(rule_id)
        update_data = payload.model_dump(exclude_unset=True, by_alias=True)

        db_update: dict[str, Any] = {}
        if "name" in update_data and update_data["name"] is not None:
            db_update["name"] = update_data["name"].strip()
        if "description" in update_data and update_data["description"] is not None:
            db_update["description"] = update_data["description"].strip()
        if "order" in update_data and update_data["order"] is not None:
            db_update["rule_order"] = update_data["order"]
        if "enabled" in update_data and update_data["enabled"] is not None:
            db_update["enabled"] = update_data["enabled"]
        if "matchType" in update_data and update_data["matchType"] is not None:
            db_update["match_type"] = update_data["matchType"]
        if "conditions" in update_data and update_data["conditions"] is not None:
            db_update["conditions"] = [
                {
                    **condition,
                    "id": condition.get("id") or f"cond-{uuid4()}",
                }
                for condition in update_data["conditions"]
            ]
        if "actions" in update_data and update_data["actions"] is not None:
            db_update["actions"] = {
                key: value
                for key, value in update_data["actions"].items()
                if value is not None
            }

        if not db_update:
            return self.get_rule(rule_id)

        response = (
            self.db.table("routing_rules")
            .update(db_update)
            .eq("id", str(rule_id))
            .execute()
        )
        if not response.data:
            raise DatabaseError("Failed to update routing rule")
        return map_routing_rule(response.data[0])

    def delete_rule(self, rule_id: UUID) -> None:
        """Delete a routing rule."""
        self.get_rule(rule_id)
        self.db.table("routing_rules").delete().eq("id", str(rule_id)).execute()

    def _get_ticket_context(self, ticket_id: UUID) -> dict[str, Any]:
        ticket_response = (
            self.db.table("tickets")
            .select("*")
            .eq("id", str(ticket_id))
            .limit(1)
            .execute()
        )
        if not ticket_response.data:
            raise TicketNotFoundError(str(ticket_id))
        ticket = ticket_response.data[0]

        customer_response = (
            self.db.table("customers")
            .select("*")
            .eq("id", ticket["customer_id"])
            .limit(1)
            .execute()
        )
        customer = customer_response.data[0] if customer_response.data else {}

        classification_response = (
            self.db.table("ticket_classifications")
            .select("language")
            .eq("ticket_id", str(ticket_id))
            .limit(1)
            .execute()
        )
        language = None
        if classification_response.data:
            language = classification_response.data[0].get("language")

        return {
            "Category": ticket.get("category"),
            "Urgency": ticket.get("priority"),
            "Sentiment": ticket.get("sentiment"),
            "CustomerPlan": customer.get("plan"),
            "Subject": ticket.get("subject"),
            "Language": language,
        }

    def _evaluate_condition(self, condition: dict[str, Any], context: dict[str, Any]) -> bool:
        field = condition.get("field")
        operator = condition.get("operator")
        expected = condition.get("value")
        actual = context.get(field)

        if actual is None:
            return False

        actual_str = str(actual)
        actual_lower = actual_str.lower()

        if operator == "equals":
            if isinstance(expected, list):
                return actual_lower in [str(item).lower() for item in expected]
            return actual_lower == str(expected).lower()

        if operator == "not_equals":
            if isinstance(expected, list):
                return actual_lower not in [str(item).lower() for item in expected]
            return actual_lower != str(expected).lower()

        if operator == "contains":
            return str(expected).lower() in actual_lower

        if operator == "contains_any":
            values = expected if isinstance(expected, list) else [expected]
            return any(str(value).lower() in actual_lower for value in values)

        if operator == "in":
            values = expected if isinstance(expected, list) else [expected]
            return actual_lower in [str(value).lower() for value in values]

        if operator == "greater_than_or_equal":
            actual_rank = PRIORITY_RANK.get(actual_lower, 0)
            expected_rank = PRIORITY_RANK.get(str(expected).lower(), 0)
            return actual_rank >= expected_rank

        return False

    def evaluate_rules(self, ticket_id: UUID) -> dict[str, Any] | None:
        """Evaluate enabled rules in order; first matching rule wins."""
        context = self._get_ticket_context(ticket_id)
        rules = [
            rule
            for rule in self.list_rules()
            if rule.get("enabled", True)
        ]

        for rule in rules:
            conditions = rule.get("conditions") or []
            if not conditions:
                continue

            results = [
                self._evaluate_condition(condition, context)
                for condition in conditions
            ]
            matched = all(results) if rule.get("matchType") == "ALL" else any(results)
            if matched:
                return {
                    "matchedRule": rule,
                    "actions": rule.get("actions") or {},
                    "context": context,
                }

        return None

    def apply_routing(self, ticket_id: UUID) -> dict[str, Any]:
        """Apply the first matching routing rule to a ticket."""
        evaluation = self.evaluate_rules(ticket_id)
        if evaluation is None:
            raise AppError(
                "No routing rule matched this ticket",
                code="NO_ROUTING_RULE_MATCHED",
                status_code=404,
            )

        rule = evaluation["matchedRule"]
        actions = evaluation["actions"]
        ticket_update: dict[str, Any] = {}

        if actions.get("assignToTeam"):
            ticket_update["assigned_team"] = actions["assignToTeam"]
        if actions.get("setPriority"):
            ticket_update["priority"] = actions["setPriority"]

        if ticket_update:
            self.db.table("tickets").update(ticket_update).eq("id", str(ticket_id)).execute()

        self.db.table("routing_rules").update(
            {
                "matches_last_30_days": (rule.get("matchesLast30Days") or 0) + 1,
                "last_triggered_at": datetime.now(UTC).isoformat(),
            }
        ).eq("id", rule["id"]).execute()

        return {
            "success": True,
            "matchedRuleId": rule["id"],
            "matchedRuleName": rule["name"],
            "actionsApplied": actions,
            "ticketUpdates": ticket_update,
        }
