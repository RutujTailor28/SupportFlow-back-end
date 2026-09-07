"""Routing rules API router."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.core.deps import get_db
from app.schemas.routing_rule import RoutingRuleCreateRequest, RoutingRuleUpdateRequest
from app.services.routing_service import RoutingService

router = APIRouter(prefix="/routing-rules", tags=["routing-rules"])


def get_routing_service(db=Depends(get_db)) -> RoutingService:  # noqa: ANN001
    """Provide a routing service bound to the Supabase admin client."""
    return RoutingService(db)


@router.get("")
async def list_routing_rules(
    service: RoutingService = Depends(get_routing_service),
) -> JSONResponse:
    """List all routing rules in evaluation order."""
    rules = service.list_rules()
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "count": len(rules),
            "data": rules,
        },
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_routing_rule(
    payload: RoutingRuleCreateRequest,
    service: RoutingService = Depends(get_routing_service),
) -> JSONResponse:
    """Create a new routing rule."""
    data = service.create_rule(payload)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "success": True,
            "message": "Routing rule created successfully",
            "data": data,
        },
    )


@router.get("/{rule_id}")
async def get_routing_rule(
    rule_id: UUID,
    service: RoutingService = Depends(get_routing_service),
) -> JSONResponse:
    """Get a single routing rule."""
    data = service.get_rule(rule_id)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "data": data,
        },
    )


@router.put("/{rule_id}")
async def update_routing_rule(
    rule_id: UUID,
    payload: RoutingRuleUpdateRequest,
    service: RoutingService = Depends(get_routing_service),
) -> JSONResponse:
    """Update a routing rule."""
    data = service.update_rule(rule_id, payload)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "Routing rule updated successfully",
            "data": data,
        },
    )


@router.delete("/{rule_id}")
async def delete_routing_rule(
    rule_id: UUID,
    service: RoutingService = Depends(get_routing_service),
) -> JSONResponse:
    """Delete a routing rule."""
    service.delete_rule(rule_id)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "Routing rule deleted successfully",
        },
    )
