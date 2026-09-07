"""Ticket API router."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse

from app.core.deps import get_db
from app.schemas.classification import ClassificationUpdateRequest
from app.schemas.escalation import EscalationAcknowledgeRequest, EscalationCreateRequest
from app.schemas.message import MessageCreateRequest
from app.schemas.ticket import TicketCreateRequest, TicketUpdateRequest
from app.services.classification_service import ClassificationService
from app.services.escalation_service import EscalationService
from app.services.message_service import MessageService
from app.services.routing_service import RoutingService
from app.services.ticket_service import TicketService

router = APIRouter(prefix="/tickets", tags=["tickets"])


def get_ticket_service(db=Depends(get_db)) -> TicketService:  # noqa: ANN001
    """Provide a ticket service bound to the Supabase admin client."""
    return TicketService(db)


def get_message_service(db=Depends(get_db)) -> MessageService:  # noqa: ANN001
    """Provide a message service bound to the Supabase admin client."""
    return MessageService(db)


def get_classification_service(db=Depends(get_db)) -> ClassificationService:  # noqa: ANN001
    """Provide a classification service bound to the Supabase admin client."""
    return ClassificationService(db)


def get_escalation_service(db=Depends(get_db)) -> EscalationService:  # noqa: ANN001
    """Provide an escalation service bound to the Supabase admin client."""
    return EscalationService(db)


def get_routing_service(db=Depends(get_db)) -> RoutingService:  # noqa: ANN001
    """Provide a routing service bound to the Supabase admin client."""
    return RoutingService(db)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_ticket(
    payload: TicketCreateRequest,
    service: TicketService = Depends(get_ticket_service),
) -> JSONResponse:
    """Create a new support ticket."""
    data = service.create_ticket(payload)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "success": True,
            "message": "Ticket created successfully",
            "data": data,
        },
    )


@router.get("")
async def list_tickets(
    status_filter: str | None = Query(default=None, alias="status"),
    category: str | None = Query(default=None),
    urgency: str | None = Query(default=None),
    sentiment: str | None = Query(default=None),
    assigned_team: str | None = Query(default=None, alias="assignedTeam"),
    search: str | None = Query(default=None),
    service: TicketService = Depends(get_ticket_service),
) -> JSONResponse:
    """List tickets with optional filters."""
    tickets = service.get_tickets(
        status=status_filter,
        category=category,
        urgency=urgency,
        sentiment=sentiment,
        assigned_team=assigned_team,
        search=search,
    )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "count": len(tickets),
            "data": tickets,
        },
    )


@router.get("/{ticket_id}/messages")
async def list_ticket_messages(
    ticket_id: UUID,
    service: MessageService = Depends(get_message_service),
) -> JSONResponse:
    """List all messages for a ticket."""
    messages = service.get_messages(ticket_id)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "count": len(messages),
            "data": messages,
        },
    )


@router.post("/{ticket_id}/messages", status_code=status.HTTP_201_CREATED)
async def create_ticket_message(
    ticket_id: UUID,
    payload: MessageCreateRequest,
    service: MessageService = Depends(get_message_service),
) -> JSONResponse:
    """Add a message to a ticket conversation."""
    data = service.create_message(ticket_id, payload)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "success": True,
            "message": "Message created successfully",
            "data": data,
        },
    )


@router.patch("/{ticket_id}/classification")
async def update_ticket_classification(
    ticket_id: UUID,
    payload: ClassificationUpdateRequest,
    service: ClassificationService = Depends(get_classification_service),
) -> JSONResponse:
    """Create or correct a ticket classification."""
    data = service.update_classification(ticket_id, payload)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "Classification updated successfully",
            "data": data,
        },
    )


@router.get("/{ticket_id}/escalations")
async def list_ticket_escalations(
    ticket_id: UUID,
    service: EscalationService = Depends(get_escalation_service),
) -> JSONResponse:
    """List all escalation records for a ticket."""
    escalations = service.get_escalations(ticket_id)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "count": len(escalations),
            "escalation": service.get_escalation_summary(ticket_id),
            "data": escalations,
        },
    )


@router.post("/{ticket_id}/escalations", status_code=status.HTTP_201_CREATED)
async def create_ticket_escalation(
    ticket_id: UUID,
    payload: EscalationCreateRequest,
    service: EscalationService = Depends(get_escalation_service),
) -> JSONResponse:
    """Manually create an escalation record for a ticket."""
    data = service.create_escalation(ticket_id, payload)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "success": True,
            "message": "Escalation created successfully",
            "data": data,
        },
    )


@router.post("/{ticket_id}/escalations/detect")
async def detect_ticket_escalations(
    ticket_id: UUID,
    service: EscalationService = Depends(get_escalation_service),
) -> JSONResponse:
    """Run keyword-based escalation detection on ticket content."""
    created = service.detect_escalations(ticket_id)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "count": len(created),
            "message": "Escalation detection completed",
            "data": created,
            "escalation": service.get_escalation_summary(ticket_id),
        },
    )


@router.patch("/{ticket_id}/escalations/{escalation_id}")
async def acknowledge_ticket_escalation(
    ticket_id: UUID,
    escalation_id: UUID,
    payload: EscalationAcknowledgeRequest,
    service: EscalationService = Depends(get_escalation_service),
) -> JSONResponse:
    """Acknowledge or update an escalation record."""
    data = service.acknowledge_escalation(ticket_id, escalation_id, payload)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "Escalation updated successfully",
            "data": data,
        },
    )


@router.get("/{ticket_id}")
async def get_ticket(
    ticket_id: UUID,
    service: TicketService = Depends(get_ticket_service),
) -> JSONResponse:
    """Get a single ticket with customer and messages."""
    data = service.get_ticket(ticket_id)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "data": data,
        },
    )


@router.patch("/{ticket_id}")
async def update_ticket(
    ticket_id: UUID,
    payload: TicketUpdateRequest,
    service: TicketService = Depends(get_ticket_service),
) -> JSONResponse:
    """Partially update a ticket."""
    data = service.update_ticket(ticket_id, payload)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "Ticket updated successfully",
            "data": data,
        },
    )


@router.post("/{ticket_id}/apply-routing")
async def apply_ticket_routing(
    ticket_id: UUID,
    routing_service: RoutingService = Depends(get_routing_service),
) -> JSONResponse:
    """Evaluate routing rules and apply the first matching rule to a ticket."""
    data = routing_service.apply_routing(ticket_id)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=data,
    )
