"""Human expert escalation handler with ticketing system integration.

Supports ServiceNow, Jira, and custom webhook integrations for seamless
handoff from AI to human experts with full context preservation.
"""

import asyncio
import time
import uuid
from dataclasses import dataclass
from enum import Enum


class EscalationPriority(str, Enum):
    """Escalation priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EscalationStatus(str, Enum):
    """Escalation lifecycle status."""

    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


@dataclass
class EscalationContext:
    """Full context for escalation handoff."""

    query: str
    ai_response: str
    retrieved_sources: list[dict]
    confidence_score: float
    session_transcript: list[dict]
    user_id: str
    tenant_id: str
    reason: str


@dataclass
class EscalationTicket:
    """Escalation ticket record."""

    id: str
    external_ticket_id: str | None
    priority: EscalationPriority
    status: EscalationStatus
    assigned_to: str | None
    created_at: float
    updated_at: float
    context: EscalationContext
    resolution_notes: str | None = None
    resolved_at: float | None = None


# In-memory escalation store (production: database)
_escalations: dict[str, EscalationTicket] = {}


class TicketingIntegration:
    """Base class for ticketing system integrations."""

    async def create_ticket(self, escalation: EscalationTicket) -> str:
        """Create ticket in external system. Override in subclasses."""
        raise NotImplementedError

    async def update_ticket(self, external_id: str, status: str, notes: str) -> None:
        """Update ticket in external system."""
        raise NotImplementedError


class ServiceNowIntegration(TicketingIntegration):
    """ServiceNow ITSM integration."""

    def __init__(
        self,
        instance_url: str,
        username: str,
        password: str,
        table_name: str = "incident",
    ) -> None:
        self.instance_url = instance_url
        self.username = username
        self.password = password
        self.table_name = table_name

    async def create_ticket(self, escalation: EscalationTicket) -> str:
        """Create incident in ServiceNow."""
        import httpx

        url = f"{self.instance_url}/api/now/table/{self.table_name}"
        auth = httpx.BasicAuth(self.username, self.password)

        short_description = f"Karena AI Escalation: {escalation.context.query[:100]}"
        description = f"""
AI Escalation from Karena AI Platform
======================================

Original Query: {escalation.context.query}

AI Response: {escalation.context.ai_response}

Confidence Score: {escalation.context.confidence_score}

Escalation Reason: {escalation.context.reason}

User ID: {escalation.context.user_id}
Tenant ID: {escalation.context.tenant_id}

Retrieved Sources:
{chr(10).join(f'- {s["title"]}' for s in escalation.context.retrieved_sources)}

Session Transcript:
{chr(10).join(f'{m["role"]}: {m["content"]}' for m in escalation.context.session_transcript[-5:])}
"""

        payload = {
            "short_description": short_description,
            "description": description,
            "urgency": self._map_priority(escalation.priority),
            "category": "knowledge_management",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    auth=auth,
                    json=payload,
                    timeout=30.0,
                )
                response.raise_for_status()
                result = response.json()
                return result.get("result", {}).get("number", "")
        except Exception:
            return ""

    def _map_priority(self, priority: EscalationPriority) -> str:
        mapping = {
            EscalationPriority.LOW: "4",
            EscalationPriority.MEDIUM: "3",
            EscalationPriority.HIGH: "2",
            EscalationPriority.CRITICAL: "1",
        }
        return mapping.get(priority, "3")


class JiraIntegration(TicketingIntegration):
    """Jira Cloud/Server integration."""

    def __init__(
        self,
        jira_url: str,
        email: str,
        api_token: str,
        project_key: str,
        issue_type: str = "Task",
    ) -> None:
        self.jira_url = jira_url
        self.email = email
        self.api_token = api_token
        self.project_key = project_key
        self.issue_type = issue_type

    async def create_ticket(self, escalation: EscalationTicket) -> str:
        """Create issue in Jira."""
        import httpx

        url = f"{self.jira_url}/rest/api/3/issue"
        auth = httpx.BasicAuth(self.email, self.api_token)

        payload = {
            "fields": {
                "project": {"key": self.project_key},
                "summary": f"Karena AI Escalation: {escalation.context.query[:100]}",
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": (
                                        f"Query: {escalation.context.query}\n\n"
                                        f"AI Response: {escalation.context.ai_response}\n\n"
                                        f"Confidence: {escalation.context.confidence_score}\n\n"
                                        f"Reason: {escalation.context.reason}"
                                    ),
                                }
                            ],
                        }
                    ],
                },
                "issuetype": {"name": self.issue_type},
                "priority": {"name": self._map_priority(escalation.priority)},
            }
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    auth=auth,
                    json=payload,
                    headers={"Accept": "application/json"},
                    timeout=30.0,
                )
                response.raise_for_status()
                result = response.json()
                return result.get("key", "")
        except Exception:
            return ""

    def _map_priority(self, priority: EscalationPriority) -> str:
        mapping = {
            EscalationPriority.LOW: "Lowest",
            EscalationPriority.MEDIUM: "Medium",
            EscalationPriority.HIGH: "High",
            EscalationPriority.CRITICAL: "Highest",
        }
        return mapping.get(priority, "Medium")


class WebhookIntegration(TicketingIntegration):
    """Generic webhook integration for custom systems."""

    def __init__(self, webhook_url: str, headers: dict[str, str] | None = None) -> None:
        self.webhook_url = webhook_url
        self.headers = headers or {}

    async def create_ticket(self, escalation: EscalationTicket) -> str:
        """Send escalation to webhook endpoint."""
        import httpx

        payload = {
            "escalation_id": escalation.id,
            "priority": escalation.priority.value,
            "query": escalation.context.query,
            "ai_response": escalation.context.ai_response,
            "confidence": escalation.context.confidence_score,
            "reason": escalation.context.reason,
            "user_id": escalation.context.user_id,
            "tenant_id": escalation.context.tenant_id,
            "sources": escalation.context.retrieved_sources,
            "transcript": escalation.context.session_transcript,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    headers=self.headers,
                    timeout=30.0,
                )
                response.raise_for_status()
                result = response.json()
                return result.get("ticket_id", escalation.id)
        except Exception:
            return escalation.id


class EscalationHandler:
    """Main escalation orchestration handler."""

    def __init__(self) -> None:
        self.integrations: dict[str, TicketingIntegration] = {}

    def register_integration(self, name: str, integration: TicketingIntegration) -> None:
        """Register a ticketing system integration."""
        self.integrations[name] = integration

    async def escalate(
        self,
        context: EscalationContext,
        priority: EscalationPriority = EscalationPriority.MEDIUM,
        integration_name: str | None = None,
    ) -> EscalationTicket:
        """Create escalation ticket and notify human expert."""
        ticket_id = str(uuid.uuid4())
        now = time.time()

        ticket = EscalationTicket(
            id=ticket_id,
            external_ticket_id=None,
            priority=priority,
            status=EscalationStatus.PENDING,
            assigned_to=None,
            created_at=now,
            updated_at=now,
            context=context,
        )

        # Create external ticket if integration available
        integration = self.integrations.get(integration_name or next(iter(self.integrations), None))
        if integration:
            external_id = await integration.create_ticket(ticket)
            if external_id:
                ticket.external_ticket_id = external_id

        _escalations[ticket_id] = ticket

        # Trigger async notifications (email, Slack, etc.)
        asyncio.create_task(self._notify_experts(ticket))

        return ticket

    async def _notify_experts(self, ticket: EscalationTicket) -> None:
        """Send notifications to on-call experts."""
        # Production: integrate with PagerDuty, OpsGenie, Slack
        print(f"[ESCALATION] Ticket {ticket.id} created with priority {ticket.priority}")

    async def update_status(
        self,
        ticket_id: str,
        status: EscalationStatus,
        assigned_to: str | None = None,
        resolution_notes: str | None = None,
    ) -> EscalationTicket | None:
        """Update escalation ticket status."""
        ticket = _escalations.get(ticket_id)
        if not ticket:
            return None

        ticket.status = status
        ticket.updated_at = time.time()

        if assigned_to:
            ticket.assigned_to = assigned_to

        if resolution_notes:
            ticket.resolution_notes = resolution_notes

        if status == EscalationStatus.RESOLVED:
            ticket.resolved_at = time.time()

        return ticket

    async def get_ticket(self, ticket_id: str) -> EscalationTicket | None:
        """Retrieve escalation ticket by ID."""
        return _escalations.get(ticket_id)

    async def list_escalations(
        self,
        tenant_id: str | None = None,
        status: EscalationStatus | None = None,
        limit: int = 50,
    ) -> list[EscalationTicket]:
        """List escalations with optional filters."""
        results = list(_escalations.values())

        if tenant_id:
            results = [t for t in results if t.context.tenant_id == tenant_id]

        if status:
            results = [t for t in results if t.status == status]

        results.sort(key=lambda t: t.created_at, reverse=True)
        return results[:limit]

    def should_escalate(
        self,
        confidence: float,
        query: str,
        has_compliance_keywords: bool = False,
        user_requested: bool = False,
    ) -> bool:
        """Determine if query should be escalated based on rules."""
        if user_requested:
            return True

        if confidence < 0.5:
            return True

        if has_compliance_keywords and confidence < 0.7:
            return True

        escalation_keywords = [
            "escalate",
            "human",
            "agent",
            "support ticket",
            "speak to person",
            "not helpful",
        ]
        if any(kw in query.lower() for kw in escalation_keywords):
            return True

        return False


# Global handler instance
_handler: EscalationHandler | None = None


def get_escalation_handler() -> EscalationHandler:
    """Get or create escalation handler instance."""
    global _handler
    if _handler is None:
        _handler = EscalationHandler()
    return _handler
