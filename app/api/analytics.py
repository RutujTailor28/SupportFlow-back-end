"""Analytics API router — placeholder endpoints for initial setup."""

from fastapi import APIRouter

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("")
async def get_analytics() -> dict[str, str]:
    """Placeholder endpoint confirming the analytics route is registered."""
    return {"message": "Analytics endpoint ready"}
