"""Compliance API routes for retention, consent, and SAR workflows."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from karena.api.gateway import Permission, requires_permission
from karena.compliance.retention import ConsentType, RetentionPolicy, SubjectAccessRequest, get_data_retention_manager

router = APIRouter()


@router.get("/compliance/retention-rules")
async def list_retention_rules():
    manager = get_data_retention_manager()
    return {"rules": [rule.dict() for rule in manager.list_retention_rules()]}


@router.post("/compliance/retention-rule")
async def add_retention_rule(rule: RetentionPolicy, _=Depends(requires_permission(Permission.ACCESS_AUDIT_LOGS))):
    manager = get_data_retention_manager()
    manager.add_retention_rule(rule)
    return {"status": "created", "rule": rule.dict()}


@router.post("/compliance/consent")
async def record_consent(consent: ConsentType, _=Depends(requires_permission(Permission.ACCESS_AUDIT_LOGS))):
    manager = get_data_retention_manager()
    manager.record_consent(consent)
    return {"status": "recorded", "consent": consent.dict()}


@router.post("/compliance/sar")
async def create_sar(request: SubjectAccessRequest, _=Depends(requires_permission(Permission.ACCESS_AUDIT_LOGS))):
    manager = get_data_retention_manager()
    manager.submit_sar(request)
    return {"status": "submitted", "request_id": request.request_id}


@router.post("/compliance/sar/{request_id}/complete")
async def complete_sar(request_id: str, _=Depends(requires_permission(Permission.ACCESS_AUDIT_LOGS))):
    manager = get_data_retention_manager()
    manager.complete_sar(request_id)
    return {"status": "completed", "request_id": request_id}


@router.post("/compliance/delete-user-data")
async def delete_user_data(user_id: str, _=Depends(requires_permission(Permission.ACCESS_AUDIT_LOGS))):
    manager = get_data_retention_manager()
    manager.delete_user_data(user_id)
    return {"status": "deleted", "user_id": user_id}
