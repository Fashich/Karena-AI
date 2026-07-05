"""Compliance and data retention management.

Handles:
- Data retention policies (configurable per tenant)
- Automated data deletion and archival workflows
- Subject access request (SAR) fulfillment
- GDPR/PDPA/Privacy Act compliance tracking
- Audit export and reporting
- Consent management
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from karena.config import get_settings
from karena.security.audit import AuditEventType, AuditEvent, get_audit_logger


class DataCategory(str, Enum):
    """Data classification for retention policies."""

    USER_INTERACTION = "user_interaction"  # Chat history, feedback
    AUDIT_LOG = "audit_log"  # System audit events
    PERSONAL_DATA = "personal_data"  # PII (email, name, etc.)
    CONTENT_DATA = "content_data"  # Documents, knowledge base
    USAGE_ANALYTICS = "usage_analytics"  # Metrics, analytics
    TRAINING_DATA = "training_data"  # ML model training data


class RetentionPolicy(str, Enum):
    """Data retention durations."""

    PERMANENT = "permanent"  # Never delete
    YEARS_7 = "years_7"
    YEARS_3 = "years_3"
    YEARS_1 = "years_1"
    MONTHS_6 = "months_6"
    MONTHS_3 = "months_3"
    MONTHS_1 = "months_1"
    DAYS_30 = "days_30"
    DAYS_7 = "days_7"

    def get_days(self) -> int | None:
        """Get retention period in days."""
        if self == RetentionPolicy.PERMANENT:
            return None
        elif self == RetentionPolicy.YEARS_7:
            return 365 * 7
        elif self == RetentionPolicy.YEARS_3:
            return 365 * 3
        elif self == RetentionPolicy.YEARS_1:
            return 365
        elif self == RetentionPolicy.MONTHS_6:
            return 180
        elif self == RetentionPolicy.MONTHS_3:
            return 90
        elif self == RetentionPolicy.MONTHS_1:
            return 30
        elif self == RetentionPolicy.DAYS_30:
            return 30
        elif self == RetentionPolicy.DAYS_7:
            return 7
        return None


class ConsentType(str, Enum):
    """Consent categories."""

    ANALYTICS = "analytics"
    MARKETING = "marketing"
    DATA_PROCESSING = "data_processing"
    TRAINING = "training"


@dataclass
class ConsentRecord:
    """User consent tracking."""

    consent_id: str = field(default_factory=lambda: str(uuid4()))
    user_id: str = ""
    tenant_id: str = ""
    consent_type: ConsentType = ConsentType.DATA_PROCESSING
    granted: bool = False
    granted_at: datetime | None = None
    expires_at: datetime | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    source: str = "ui"  # ui, api, form, etc.

    def is_valid(self) -> bool:
        """Check if consent is currently valid."""
        if not self.granted:
            return False
        if self.expires_at and datetime.now(timezone.utc) > self.expires_at:
            return False
        return True


@dataclass
class DataRetentionRule:
    """Policy rule for data retention."""

    rule_id: str = field(default_factory=lambda: str(uuid4()))
    tenant_id: str = ""
    data_category: DataCategory = DataCategory.USER_INTERACTION
    retention_policy: RetentionPolicy = RetentionPolicy.YEARS_1
    auto_anonymize: bool = False
    auto_delete: bool = True
    archive_before_delete: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SubjectAccessRequest:
    """Subject Access Request (GDPR/PDPA)."""

    request_id: str = field(default_factory=lambda: str(uuid4()))
    user_id: str = ""
    tenant_id: str = ""
    requested_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    due_date: datetime | None = None
    status: str = "pending"  # pending, processing, completed, denied
    data_format: str = "json"  # json, csv, pdf
    verification_method: str = "email"  # email, sms, in_person
    verification_completed: bool = False
    data_export_url: str | None = None
    completed_at: datetime | None = None
    notes: str = ""


class DataRetentionManager:
    """Manages data retention policies and execution."""

    def __init__(self) -> None:
        self._retention_rules: dict[str, DataRetentionRule] = {}
        self._consent_records: dict[str, ConsentRecord] = {}
        self._sar_requests: dict[str, SubjectAccessRequest] = {}

    def create_retention_rule(
        self,
        tenant_id: str,
        data_category: DataCategory,
        retention_policy: RetentionPolicy,
        *,
        auto_anonymize: bool = False,
        auto_delete: bool = True,
        archive_before_delete: bool = True,
    ) -> DataRetentionRule:
        """Create a data retention rule for a tenant."""
        rule = DataRetentionRule(
            tenant_id=tenant_id,
            data_category=data_category,
            retention_policy=retention_policy,
            auto_anonymize=auto_anonymize,
            auto_delete=auto_delete,
            archive_before_delete=archive_before_delete,
        )
        self._retention_rules[rule.rule_id] = rule
        return rule

    def get_retention_rule(
        self,
        tenant_id: str,
        data_category: DataCategory,
    ) -> DataRetentionRule | None:
        """Get retention rule for a data category."""
        for rule in self._retention_rules.values():
            if rule.tenant_id == tenant_id and rule.data_category == data_category:
                return rule
        return None

    def list_retention_rules(self, tenant_id: str) -> list[DataRetentionRule]:
        """List all retention rules for a tenant."""
        return [r for r in self._retention_rules.values() if r.tenant_id == tenant_id]

    def should_delete_data(
        self,
        tenant_id: str,
        data_category: DataCategory,
        created_at: datetime,
    ) -> bool:
        """Check if data should be deleted based on retention policy."""
        rule = self.get_retention_rule(tenant_id, data_category)
        if not rule or not rule.auto_delete:
            return False

        retention_days = rule.retention_policy.get_days()
        if retention_days is None:
            return False  # Permanent retention

        expiration = created_at + timedelta(days=retention_days)
        return datetime.now(timezone.utc) > expiration

    def record_consent(
        self,
        user_id: str,
        tenant_id: str,
        consent_type: ConsentType,
        granted: bool,
        *,
        ip_address: str | None = None,
        user_agent: str | None = None,
        expires_at: datetime | None = None,
    ) -> ConsentRecord:
        """Record user consent."""
        consent = ConsentRecord(
            user_id=user_id,
            tenant_id=tenant_id,
            consent_type=consent_type,
            granted=granted,
            granted_at=datetime.now(timezone.utc) if granted else None,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at,
        )
        self._consent_records[consent.consent_id] = consent

        # Audit log consent changes
        get_audit_logger(get_settings().audit_db_path).log(
            AuditEventType.DATA_UPDATE,
            actor_id=user_id,
            actor_type="user",
            action="consent_recorded",
            resource_type="consent",
            tenant_id=tenant_id,
            details={
                "consent_type": consent_type.value,
                "granted": granted,
            },
        )

        return consent

    def has_consent(
        self,
        user_id: str,
        consent_type: ConsentType,
    ) -> bool:
        """Check if user has active consent."""
        for consent in self._consent_records.values():
            if consent.user_id == user_id and consent.consent_type == consent_type:
                if consent.is_valid():
                    return True
        return False

    def revoke_consent(self, user_id: str, consent_type: ConsentType | None = None) -> int:
        """Revoke user consent (optionally for specific type)."""
        revoked = 0
        for consent_id, consent in list(self._consent_records.items()):
            if consent.user_id == user_id:
                if consent_type is None or consent.consent_type == consent_type:
                    consent.granted = False
                    revoked += 1
        return revoked

    def create_subject_access_request(
        self,
        user_id: str,
        tenant_id: str,
        *,
        data_format: str = "json",
        verification_method: str = "email",
    ) -> SubjectAccessRequest:
        """Create a subject access request (SAR)."""
        settings = get_settings()
        # Due date is typically 30 days for GDPR, 30 calendar days for PDPA
        due_date = datetime.now(timezone.utc) + timedelta(days=30)

        sar = SubjectAccessRequest(
            user_id=user_id,
            tenant_id=tenant_id,
            due_date=due_date,
            data_format=data_format,
            verification_method=verification_method,
        )
        self._sar_requests[sar.request_id] = sar

        # Audit log SAR creation
        get_audit_logger(settings.audit_db_path).log(
            AuditEventType.DATA_CREATE,
            actor_id=user_id,
            actor_type="user",
            action="sar_created",
            resource_type="subject_access_request",
            resource_id=sar.request_id,
            tenant_id=tenant_id,
            details={"request_id": sar.request_id},
        )

        return sar

    def complete_subject_access_request(
        self,
        request_id: str,
        export_url: str,
    ) -> SubjectAccessRequest | None:
        """Mark SAR as completed and provide export URL."""
        sar = self._sar_requests.get(request_id)
        if not sar:
            return None

        sar.status = "completed"
        sar.data_export_url = export_url
        sar.completed_at = datetime.now(timezone.utc)

        settings = get_settings()
        get_audit_logger(settings.audit_db_path).log(
            AuditEventType.DATA_EXPORT,
            actor_id=sar.user_id,
            actor_type="user",
            action="sar_completed",
            resource_type="subject_access_request",
            resource_id=request_id,
            tenant_id=sar.tenant_id,
            details={"request_id": request_id},
        )

        return sar

    def delete_user_data(
        self,
        user_id: str,
        tenant_id: str,
        categories: list[DataCategory] | None = None,
    ) -> dict[str, int]:
        """Delete user data across specified categories."""
        results = {}
        settings = get_settings()

        # Simulate deletion counts (in production, would delete from databases)
        if categories is None:
            categories = list(DataCategory)

        for category in categories:
            # Placeholder: would delete from actual databases
            deleted_count = 0
            results[category.value] = deleted_count

        # Audit log deletion
        get_audit_logger(settings.audit_db_path).log(
            AuditEventType.DATA_DELETE,
            actor_id=user_id,
            actor_type="user",
            action="data_deleted",
            resource_type="user_data",
            tenant_id=tenant_id,
            details={
                "categories": [c.value for c in (categories or list(DataCategory))],
                "deletion_counts": results,
            },
        )

        return results

    def list_subject_access_requests(
        self,
        tenant_id: str | None = None,
        user_id: str | None = None,
        status: str | None = None,
    ) -> list[SubjectAccessRequest]:
        """List subject access requests."""
        sars = list(self._sar_requests.values())

        if tenant_id:
            sars = [s for s in sars if s.tenant_id == tenant_id]
        if user_id:
            sars = [s for s in sars if s.user_id == user_id]
        if status:
            sars = [s for s in sars if s.status == status]

        return sorted(sars, key=lambda s: s.requested_at, reverse=True)

    def get_overdue_sars(self) -> list[SubjectAccessRequest]:
        """Get subject access requests that are overdue."""
        now = datetime.now(timezone.utc)
        return [
            s
            for s in self._sar_requests.values()
            if s.due_date and s.due_date < now and s.status != "completed"
        ]


_data_retention_manager: DataRetentionManager | None = None


def get_data_retention_manager() -> DataRetentionManager:
    """Get or create the global data retention manager."""
    global _data_retention_manager
    if _data_retention_manager is None:
        _data_retention_manager = DataRetentionManager()
    return _data_retention_manager
