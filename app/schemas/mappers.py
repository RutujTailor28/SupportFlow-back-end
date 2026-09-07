"""Map database records (snake_case) to API responses (camelCase)."""

from __future__ import annotations

from typing import Any


def map_customer(row: dict[str, Any]) -> dict[str, Any]:
    """Map a customers table row to a frontend-compatible customer object."""
    return {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "avatar": row.get("avatar_url"),
        "company": row.get("company"),
        "plan": row.get("plan", "Free"),
        "isVip": row.get("is_vip", False),
        "joinedDate": row.get("joined_date"),
    }


def map_message(row: dict[str, Any]) -> dict[str, Any]:
    """Map a ticket_messages table row to a frontend-compatible message object."""
    return {
        "id": row["id"],
        "senderType": row["sender_type"],
        "senderName": row["sender_name"],
        "senderAvatar": row.get("sender_avatar"),
        "content": row["body"],
        "timestamp": row["created_at"],
        "direction": row["direction"],
        "isAiGenerated": row.get("is_ai_generated", False),
        "aiConfidence": float(row["ai_confidence"]) if row.get("ai_confidence") is not None else None,
    }


def map_classification(
    classification: dict[str, Any],
    correction: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Map classification row to frontend-compatible AIClassification shape."""
    original = {
        "id": classification["id"],
        "ticketId": classification["ticket_id"],
        "category": classification.get("category"),
        "subcategory": classification.get("subcategory"),
        "urgency": classification.get("urgency"),
        "sentiment": classification.get("sentiment"),
        "language": classification.get("language"),
        "intentSummary": classification.get("intent_summary"),
        "entities": classification.get("entities") or [],
        "confidence": float(classification["confidence"])
        if classification.get("confidence") is not None
        else None,
        "humanCorrected": classification.get("human_corrected", False),
        "source": classification.get("source", "ai"),
        "createdAt": classification.get("created_at"),
        "updatedAt": classification.get("updated_at"),
    }

    if not correction:
        return original

    effective = original.copy()
    field_map = {
        "category": "category",
        "subcategory": "subcategory",
        "urgency": "urgency",
        "sentiment": "sentiment",
        "language": "language",
        "intent_summary": "intentSummary",
        "entities": "entities",
        "confidence": "confidence",
    }
    for db_field, api_field in field_map.items():
        if correction.get(db_field) is not None:
            value = correction[db_field]
            if db_field == "confidence" and value is not None:
                value = float(value)
            effective[api_field] = value

    effective["humanCorrected"] = True
    effective["originalClassification"] = {
        "category": classification.get("category"),
        "subcategory": classification.get("subcategory"),
        "urgency": classification.get("urgency"),
        "sentiment": classification.get("sentiment"),
        "language": classification.get("language"),
        "intentSummary": classification.get("intent_summary"),
        "entities": classification.get("entities") or [],
        "confidence": float(classification["confidence"])
        if classification.get("confidence") is not None
        else None,
    }
    effective["latestCorrection"] = {
        "id": correction["id"],
        "notes": correction.get("notes"),
        "createdAt": correction.get("created_at"),
    }
    return effective


def map_escalation(row: dict[str, Any]) -> dict[str, Any]:
    """Map a ticket_escalations row to a frontend-compatible escalation object."""
    return {
        "id": row["id"],
        "ticketId": row["ticket_id"],
        "reason": row["reason"],
        "triggerPhrases": row.get("trigger_phrases") or [],
        "acknowledged": row.get("acknowledged", False),
        "source": row.get("source", "manual"),
        "notes": row.get("notes"),
        "escalatedAt": row.get("created_at"),
        "acknowledgedAt": row.get("acknowledged_at"),
    }


def map_escalation_summary(escalations: list[dict[str, Any]]) -> dict[str, Any]:
    """Build frontend EscalationDetails from a list of escalation records."""
    if not escalations:
        return {
            "isEscalated": False,
            "reason": None,
            "triggerPhrases": [],
            "acknowledged": False,
            "escalatedAt": None,
        }

    active = [item for item in escalations if not item.get("acknowledged", False)]
    primary = active[0] if active else escalations[0]

    all_phrases: list[str] = []
    for item in escalations:
        all_phrases.extend(item.get("triggerPhrases") or [])

    return {
        "isEscalated": len(active) > 0,
        "reason": primary.get("reason"),
        "triggerPhrases": list(dict.fromkeys(all_phrases)),
        "acknowledged": len(active) == 0 and len(escalations) > 0,
        "escalatedAt": escalations[0].get("escalatedAt"),
    }


def map_routing_rule(row: dict[str, Any]) -> dict[str, Any]:
    """Map a routing_rules row to a frontend-compatible routing rule object."""
    return {
        "id": row["id"],
        "name": row["name"],
        "description": row.get("description") or "",
        "order": row.get("rule_order", 1),
        "enabled": row.get("enabled", True),
        "matchType": row.get("match_type", "ALL"),
        "conditions": row.get("conditions") or [],
        "actions": row.get("actions") or {},
        "matchesLast30Days": row.get("matches_last_30_days", 0),
        "lastTriggered": row.get("last_triggered_at"),
    }


def map_kb_article(row: dict[str, Any]) -> dict[str, Any]:
    """Map a kb_articles row to a frontend-compatible KBArticle object."""
    return {
        "id": row["id"],
        "title": row["title"],
        "slug": row["slug"],
        "category": row["category"],
        "tags": row.get("tags") or [],
        "content": row["content"],
        "summary": row.get("summary") or "",
        "status": row.get("status", "draft"),
        "lastIndexed": row.get("last_indexed_at"),
        "lastUpdated": row.get("updated_at"),
        "chunksCount": row.get("chunks_count", 0),
        "embeddingModel": row.get("embedding_model", "text-embedding-004"),
        "viewCount": row.get("view_count", 0),
        "helpfulVotes": row.get("helpful_votes", 0),
        "aiUsageCount": row.get("ai_usage_count", 0),
    }


def map_ticket_summary(ticket: dict[str, Any], customer: dict[str, Any]) -> dict[str, Any]:
    """Map ticket + customer rows to a list/create response item."""
    return {
        "id": ticket["id"],
        "ticketNumber": ticket["ticket_number"],
        "customerName": customer["name"],
        "customerEmail": customer["email"],
        "subject": ticket["subject"],
        "body": ticket["body"],
        "status": ticket["status"],
        "priority": ticket["priority"],
        "channel": ticket["channel"],
        "category": ticket.get("category"),
        "sentiment": ticket.get("sentiment"),
        "assignedTeam": ticket.get("assigned_team"),
        "createdAt": ticket["created_at"],
        "updatedAt": ticket.get("updated_at"),
        "slaDueAt": ticket.get("sla_due_at"),
    }


def map_ticket_detail(
    ticket: dict[str, Any],
    customer: dict[str, Any],
    messages: list[dict[str, Any]],
    classification: dict[str, Any] | None = None,
    escalations: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Map ticket detail with nested customer, messages, classification, and escalations."""
    ticket_payload = {
        "id": ticket["id"],
        "ticketNumber": ticket["ticket_number"],
        "subject": ticket["subject"],
        "body": ticket["body"],
        "status": ticket["status"],
        "priority": ticket["priority"],
        "channel": ticket["channel"],
        "category": ticket.get("category"),
        "sentiment": ticket.get("sentiment"),
        "assignedTeam": ticket.get("assigned_team"),
        "assignedAgentId": ticket.get("assigned_agent_id"),
        "createdAt": ticket["created_at"],
        "updatedAt": ticket.get("updated_at"),
        "firstResponseAt": ticket.get("first_response_at"),
        "resolvedAt": ticket.get("resolved_at"),
        "slaDueAt": ticket.get("sla_due_at"),
    }

    payload: dict[str, Any] = {
        "ticket": ticket_payload,
        "customer": map_customer(customer),
        "messages": [map_message(message) for message in messages],
    }
    if classification is not None:
        payload["aiClassification"] = classification
    if escalations is not None:
        payload["escalations"] = escalations
        payload["escalation"] = map_escalation_summary(escalations)
    return payload
