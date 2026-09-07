"""Security helpers for future authentication.

This module is intentionally minimal. Full authentication will be added later and
should cover:

* Supabase JWT validation
* Current user extraction from request headers
* FastAPI dependencies for protected routes

Do not implement authentication logic here yet.
"""

from typing import Any


async def get_current_user_placeholder() -> dict[str, Any]:
    """Placeholder dependency for protected routes.

    Future implementation will validate a Supabase JWT and return the
    authenticated user payload.
    """
    return {
        "id": None,
        "authenticated": False,
        "message": "Authentication not implemented yet",
    }
