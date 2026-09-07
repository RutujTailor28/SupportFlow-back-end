"""Database schema verification helpers."""

from __future__ import annotations

from typing import Any

from app.db.supabase import get_supabase_admin_client

CORE_TABLES: tuple[str, ...] = (
    "profiles",
    "customers",
    "tickets",
    "ticket_messages",
    "ticket_classifications",
    "classification_corrections",
    "ticket_escalations",
    "routing_rules",
    "kb_articles",
)


def verify_core_schema() -> dict[str, Any]:
    """Check that all Phase 2 core tables exist and are queryable."""
    client = get_supabase_admin_client()
    if client is None:
        return {
            "success": False,
            "tables": {},
            "message": "Supabase admin client is not configured",
        }

    table_status: dict[str, str] = {}
    all_ok = True

    for table in CORE_TABLES:
        try:
            client.table(table).select("id").limit(1).execute()
            table_status[table] = "ok"
        except Exception as exc:  # noqa: BLE001 - surface PostgREST errors
            all_ok = False
            error_text = str(exc)
            if "PGRST205" in error_text or "Could not find the table" in error_text:
                table_status[table] = "missing"
            else:
                table_status[table] = "error"

    return {
        "success": all_ok,
        "tables": table_status,
        "message": "All core tables are ready" if all_ok else "One or more core tables are missing",
    }
