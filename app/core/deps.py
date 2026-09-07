"""FastAPI dependencies shared across route handlers."""

from typing import Any

from fastapi import HTTPException, status

from app.db.supabase import get_supabase_admin_client, get_supabase_client


def get_db() -> Any:
    """Return the Supabase admin client for backend database operations."""
    client = get_supabase_admin_client()
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "detail": "Database is not configured. Add Supabase credentials to .env",
                "code": "SUPABASE_NOT_CONFIGURED",
            },
        )
    return client


def get_public_db() -> Any:
    """Return the Supabase anon client for RLS-scoped operations."""
    client = get_supabase_client()
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "detail": "Database is not configured. Add Supabase credentials to .env",
                "code": "SUPABASE_NOT_CONFIGURED",
            },
        )
    return client
