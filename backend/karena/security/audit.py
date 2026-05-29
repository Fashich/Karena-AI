"""Karena AI Audit Logging System.

Provides comprehensive audit trail capabilities for compliance,
security monitoring, and forensic analysis.
"""

import json
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from pathlib import Path
import sqlite3


class AuditEventType(str, Enum):
    """Types of audit events."""

    # Authentication & Authorization
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    PERMISSION_DENIED = "permission_denied"
    ROLE_CHANGED = "role_changed"

    # Data Access
    DATA_ACCESS = "data_access"
    DATA_QUERY = "data_query"
    DATA_EXPORT = "data_export"
    DATA_DOWNLOAD = "data_download"

    # Data Modification
    DATA_CREATE = "data_create"
    DATA_UPDATE = "data_update"
    DATA_DELETE = "data_delete"

    # Security Events
    DLP_VIOLATION = "dlp_violation"
    PII_DETECTED = "pii_detected"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"

    # System Events
    CONFIG_CHANGE = "config_change"
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    BACKUP_CREATED = "backup_created"

    # Compliance
    DATA_RETENTION_APPLIED = "data_retention_applied"
    DATA_ERASURE_REQUEST = "data_erasure_request"
    DATA_ERASURE_COMPLETED = "data_erasure_completed"
    ACCESS_REVIEW = "access_review"

    # RAG Specific
    RAG_QUERY = "rag_query"
    RAG_RETRIEVAL = "rag_retrieval"
    RAG_RESPONSE_GENERATED = "rag_response_generated"
    ESCALATION_CREATED = "escalation_created"


class EventSeverity(str, Enum):
    """Event severity levels."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Represents a single audit event."""

    event_id: str
    timestamp: str
    event_type: AuditEventType
    severity: EventSeverity
    actor_id: str
    actor_type: str  # user, system, service
    action: str
    resource_type: str | None = None
    resource_id: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
    source_ip: str | None = None
    user_agent: str | None = None
    tenant_id: str | None = None
    session_id: str | None = None
    correlation_id: str | None = None
    outcome: str = "success"  # success, failure, partial
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict())


class AuditLogger:
    """Comprehensive audit logging system for compliance and security."""

    def __init__(self, db_path: str = ":memory:", retention_days: int = 90) -> None:
        self.db_path = db_path
        self.retention_days = retention_days
        self._init_database()

    def _init_database(self) -> None:
        """Initialize the audit log database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Main audit events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_events (
                event_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                actor_id TEXT NOT NULL,
                actor_type TEXT NOT NULL,
                action TEXT NOT NULL,
                resource_type TEXT,
                resource_id TEXT,
                details TEXT,
                source_ip TEXT,
                user_agent TEXT,
                tenant_id TEXT,
                session_id TEXT,
                correlation_id TEXT,
                outcome TEXT NOT NULL,
                error_message TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Indexes for common queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_timestamp
            ON audit_events(timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_actor
            ON audit_events(actor_id, actor_type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_event_type
            ON audit_events(event_type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_tenant
            ON audit_events(tenant_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_resource
            ON audit_events(resource_type, resource_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_session
            ON audit_events(session_id)
        """)

        # Compliance reports table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS compliance_reports (
                report_id TEXT PRIMARY KEY,
                report_type TEXT NOT NULL,
                generated_at TEXT NOT NULL,
                period_start TEXT NOT NULL,
                period_end TEXT NOT NULL,
                report_data TEXT,
                status TEXT DEFAULT 'generated'
            )
        """)

        conn.commit()
        conn.close()

    def log(
        self,
        event_type: AuditEventType,
        actor_id: str,
        actor_type: str,
        action: str,
        severity: EventSeverity = EventSeverity.INFO,
        resource_type: str | None = None,
        resource_id: str | None = None,
        details: dict[str, Any] | None = None,
        source_ip: str | None = None,
        user_agent: str | None = None,
        tenant_id: str | None = None,
        session_id: str | None = None,
        correlation_id: str | None = None,
        outcome: str = "success",
        error_message: str | None = None,
    ) -> AuditEvent:
        """Log an audit event."""
        from uuid import uuid4

        event = AuditEvent(
            event_id=str(uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=event_type,
            severity=severity,
            actor_id=actor_id,
            actor_type=actor_type,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            source_ip=source_ip,
            user_agent=user_agent,
            tenant_id=tenant_id,
            session_id=session_id,
            correlation_id=correlation_id,
            outcome=outcome,
            error_message=error_message,
        )

        self._persist_event(event)
        return event

    def _persist_event(self, event: AuditEvent) -> None:
        """Persist event to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO audit_events (
                event_id, timestamp, event_type, severity,
                actor_id, actor_type, action, resource_type, resource_id,
                details, source_ip, user_agent, tenant_id, session_id,
                correlation_id, outcome, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                event.event_id,
                event.timestamp,
                event.event_type.value,
                event.severity.value,
                event.actor_id,
                event.actor_type,
                event.action,
                event.resource_type,
                event.resource_id,
                json.dumps(event.details),
                event.source_ip,
                event.user_agent,
                event.tenant_id,
                event.session_id,
                event.correlation_id,
                event.outcome,
                event.error_message,
            ),
        )

        conn.commit()
        conn.close()

    def query_events(
        self,
        start_time: str | None = None,
        end_time: str | None = None,
        event_type: AuditEventType | None = None,
        actor_id: str | None = None,
        tenant_id: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        severity: EventSeverity | None = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> list[AuditEvent]:
        """Query audit events with filters."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        conditions = []
        params = []

        if start_time:
            conditions.append("timestamp >= ?")
            params.append(start_time)

        if end_time:
            conditions.append("timestamp <= ?")
            params.append(end_time)

        if event_type:
            conditions.append("event_type = ?")
            params.append(event_type.value)

        if actor_id:
            conditions.append("actor_id = ?")
            params.append(actor_id)

        if tenant_id:
            conditions.append("tenant_id = ?")
            params.append(tenant_id)

        if resource_type:
            conditions.append("resource_type = ?")
            params.append(resource_type)

        if resource_id:
            conditions.append("resource_id = ?")
            params.append(resource_id)

        if severity:
            conditions.append("severity = ?")
            params.append(severity.value)

        query = "SELECT * FROM audit_events"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_event(row) for row in rows]

    def _row_to_event(self, row: tuple) -> AuditEvent:
        """Convert database row to AuditEvent."""
        return AuditEvent(
            event_id=row[0],
            timestamp=row[1],
            event_type=AuditEventType(row[2]),
            severity=EventSeverity(row[3]),
            actor_id=row[4],
            actor_type=row[5],
            action=row[6],
            resource_type=row[7],
            resource_id=row[8],
            details=json.loads(row[9]) if row[9] else {},
            source_ip=row[10],
            user_agent=row[11],
            tenant_id=row[12],
            session_id=row[13],
            correlation_id=row[14],
            outcome=row[15],
            error_message=row[16],
        )

    def get_event_by_id(self, event_id: str) -> AuditEvent | None:
        """Get a specific event by ID."""
        events = self.query_events(limit=1)
        for event in events:
            if event.event_id == event_id:
                return event
        return None

    def export_events(
        self,
        start_time: str,
        end_time: str,
        format: str = "json",
    ) -> str:
        """Export events for compliance reporting."""
        events = self.query_events(start_time=start_time, end_time=end_time, limit=100000)

        if format == "json":
            return json.dumps([e.to_dict() for e in events], indent=2)
        elif format == "csv":
            import csv
            import io

            output = io.StringIO()
            if events:
                writer = csv.DictWriter(output, fieldnames=events[0].to_dict().keys())
                writer.writeheader()
                for event in events:
                    writer.writerow(event.to_dict())

            return output.getvalue()

        raise ValueError(f"Unsupported export format: {format}")

    def apply_retention_policy(self) -> int:
        """Apply retention policy to delete old events."""
        from datetime import timedelta

        cutoff_date = (datetime.now(timezone.utc) - timedelta(days=self.retention_days)).isoformat()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM audit_events WHERE timestamp < ?", (cutoff_date,))

        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()

        return deleted_count

    def generate_compliance_report(
        self,
        report_type: str,
        period_start: str,
        period_end: str,
    ) -> dict[str, Any]:
        """Generate compliance report for auditors."""
        from uuid import uuid4

        events = self.query_events(
            start_time=period_start,
            end_time=period_end,
            limit=100000,
        )

        # Aggregate statistics
        stats = {
            "total_events": len(events),
            "events_by_type": {},
            "events_by_severity": {},
            "unique_actors": set(),
            "security_events": 0,
            "compliance_events": 0,
        }

        for event in events:
            # Count by type
            type_key = event.event_type.value
            stats["events_by_type"][type_key] = stats["events_by_type"].get(type_key, 0) + 1

            # Count by severity
            sev_key = event.severity.value
            stats["events_by_severity"][sev_key] = stats["events_by_severity"].get(sev_key, 0) + 1

            # Track unique actors
            stats["unique_actors"].add(event.actor_id)

            # Count security events
            if event.event_type in [
                AuditEventType.DLP_VIOLATION,
                AuditEventType.PII_DETECTED,
                AuditEventType.PERMISSION_DENIED,
                AuditEventType.SUSPICIOUS_ACTIVITY,
            ]:
                stats["security_events"] += 1

            # Count compliance events
            if event.event_type in [
                AuditEventType.DATA_ERASURE_REQUEST,
                AuditEventType.DATA_ERASURE_COMPLETED,
                AuditEventType.DATA_RETENTION_APPLIED,
                AuditEventType.ACCESS_REVIEW,
            ]:
                stats["compliance_events"] += 1

        # Convert set to count
        stats["unique_actors"] = len(stats["unique_actors"])

        report = {
            "report_id": str(uuid4()),
            "report_type": report_type,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "period_start": period_start,
            "period_end": period_end,
            "statistics": stats,
            "events_sample": [e.to_dict() for e in events[:100]],  # First 100 events
        }

        # Store report
        self._store_report(report)

        return report

    def _store_report(self, report: dict) -> None:
        """Store compliance report in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO compliance_reports (
                report_id, report_type, generated_at, period_start, period_end, report_data
            ) VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                report["report_id"],
                report["report_type"],
                report["generated_at"],
                report["period_start"],
                report["period_end"],
                json.dumps(report),
            ),
        )

        conn.commit()
        conn.close()


# Global audit logger instance
_audit_logger: AuditLogger | None = None


def get_audit_logger(db_path: str = ":memory:", retention_days: int = 90) -> AuditLogger:
    """Get or create the global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger(db_path=db_path, retention_days=retention_days)
    return _audit_logger
