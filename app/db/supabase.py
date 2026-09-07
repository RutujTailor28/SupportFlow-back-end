"""Supabase client initialization and connection helpers."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_supabase_client: Any | None = None
_supabase_admin_client: Any | None = None


def is_supabase_configured() -> bool:
    """Return True when Supabase URL and at least one API key are present."""
    return bool(settings.SUPABASE_URL and (settings.SUPABASE_ANON_KEY or settings.SUPABASE_SERVICE_ROLE_KEY))


def _create_client(api_key: str) -> Any:
    """Create a Supabase client with the given API key."""
    from supabase import create_client

    return create_client(settings.SUPABASE_URL, api_key)


def get_supabase_client() -> Any | None:
    """Return the public Supabase client (anon/publishable key).

    Use this for operations that should respect Row Level Security.
    """
    global _supabase_client

    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        logger.warning("Supabase anon key is not configured.")
        return None

    if _supabase_client is None:
        try:
            _supabase_client = _create_client(settings.SUPABASE_ANON_KEY)
            logger.info("Supabase anon client initialized.")
        except Exception as exc:
            logger.error("Failed to initialize Supabase anon client: %s", exc)
            return None

    return _supabase_client


def get_supabase_admin_client() -> Any | None:
    """Return the admin Supabase client (service role / secret key).

    Use this for trusted backend operations that bypass RLS.
    """
    global _supabase_admin_client

    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        logger.warning("Supabase service role key is not configured.")
        return None

    if _supabase_admin_client is None:
        try:
            _supabase_admin_client = _create_client(settings.SUPABASE_SERVICE_ROLE_KEY)
            logger.info("Supabase admin client initialized.")
        except Exception as exc:
            logger.error("Failed to initialize Supabase admin client: %s", exc)
            return None

    return _supabase_admin_client


async def check_supabase_connection() -> dict[str, str | bool]:
    """Verify Supabase credentials by calling the REST API."""
    if not is_supabase_configured():
        return {
            "configured": False,
            "connected": False,
            "message": "Supabase credentials are missing in .env",
        }

    api_key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY
    rest_url = f"{settings.SUPABASE_URL.rstrip('/')}/rest/v1/"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                rest_url,
                headers={
                    "apikey": api_key,
                    "Authorization": f"Bearer {api_key}",
                },
            )

        if response.status_code < 500:
            return {
                "configured": True,
                "connected": True,
                "message": "Supabase connection successful",
            }

        return {
            "configured": True,
            "connected": False,
            "message": f"Supabase returned status {response.status_code}",
        }
    except httpx.HTTPError as exc:
        return {
            "configured": True,
            "connected": False,
            "message": f"Supabase connection failed: {exc}",
        }


def init_supabase_clients() -> None:
    """Eagerly initialize Supabase clients on application startup."""
    if not is_supabase_configured():
        logger.warning(
            "Supabase is not configured. Set SUPABASE_URL and keys in backend/.env"
        )
        return

    get_supabase_client()
    get_supabase_admin_client()
