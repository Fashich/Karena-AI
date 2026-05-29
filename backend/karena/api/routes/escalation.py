"""API routes for escalation management."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from karena.api.gateway import (
    get_current_user,
    requires_permission,
    Permission,
    TokenPayload,
)
from karena.api.schemas import SourceCitation
from karena.agents.escalation import (
    get_escalation_handler,
    EscalationContext,
    EscalationPriority,
    EscalationStatus,
)

router = APIRouter()


class EscalationRequest(BaseModel):
    session_id: str
    query: str
    ai_response: str
    sources: list[SourceCitation]
    confidence: float
    reason: str
    priority: str = "medium"


class EscalationResponse(BaseModel):
    ticket_id: str
    external_ticket_id: str | None
    status: str
    priority: str
    created_at: float
    message: str


@router.post("/escalate", response_model=EscalationResponse)
async def create_escalation(
    request: EscalationRequest,
    current_user: TokenPayload = Depends(get_current_user),
):
    """Create escalation ticket for human expert review."""
    handler = get_escalation_handler()

    context = EscalationContext(
        query=request.query,
        ai_response=request.ai_response,
        retrieved_sources=[s.model_dump() for s in request.sources],
        confidence_score=request.confidence,
        session_transcript=[],
        user_id=current_user.sub,
        tenant_id=current_user.tenant_id,
        reason=request.reason,
    )

    priority_map = {
        "low": EscalationPriority.LOW,
        "medium": EscalationPriority.MEDIUM,
        "high": EscalationPriority.HIGH,
        "critical": EscalationPriority.CRITICAL,
    }
    priority = priority_map.get(request.priority.lower(), EscalationPriority.MEDIUM)

    ticket = await handler.escalate(context, priority=priority)

    return EscalationResponse(
        ticket_id=ticket.id,
        external_ticket_id=ticket.external_ticket_id,
        status=ticket.status.value,
        priority=ticket.priority.value,
        created_at=ticket.created_at,
        message="Escalation created successfully. Our team will respond shortly.",
    )


@router.get("/escalations")
async def list_escalations(
    status: str | None = None,
    limit: int = 50,
    current_user: TokenPayload = Depends(
        requires_permission(Permission.VIEW_ANALYTICS)
    ),
):
    """List escalations for tenant (requires analytics permission)."""
    handler = get_escalation_handler()

    status_filter = None
    if status:
        try:
            status_filter = EscalationStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    tickets = await handler.list_escalations(
        tenant_id=current_user.tenant_id,
        status=status_filter,
        limit=limit,
    )

    return {
        "escalations": [
            {
                "ticket_id": t.id,
                "external_ticket_id": t.external_ticket_id,
                "status": t.status.value,
                "priority": t.priority.value,
                "query_preview": t.context.query[:100],
                "created_at": t.created_at,
                "assigned_to": t.assigned_to,
            }
            for t in tickets
        ],
        "total": len(tickets),
    }


@router.get("/escalations/{ticket_id}")
async def get_escalation(
    ticket_id: str,
    current_user: TokenPayload = Depends(get_current_user),
):
    """Get details of a specific escalation ticket."""
    handler = get_escalation_handler()
    ticket = await handler.get_ticket(ticket_id)

    if not ticket:
        raise HTTPException(status_code=404, detail="Escalation not found")

    if ticket.context.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return {
        "ticket_id": ticket.id,
        "external_ticket_id": ticket.external_ticket_id,
        "status": ticket.status.value,
        "priority": ticket.priority.value,
        "context": {
            "query": ticket.context.query,
            "ai_response": ticket.context.ai_response,
            "confidence": ticket.context.confidence_score,
            "reason": ticket.context.reason,
        },
        "resolution_notes": ticket.resolution_notes,
        "created_at": ticket.created_at,
        "updated_at": ticket.updated_at,
        "resolved_at": ticket.resolved_at,
    }
