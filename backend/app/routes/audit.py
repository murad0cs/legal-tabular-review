from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.audit_service import AuditService
from ..schemas import AuditLogListResponse, AuditLogResponse

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("/projects/{project_id}", response_model=AuditLogListResponse)
def get_audit_logs_for_project(
    project_id: int,
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):
    """Get audit logs for a project."""
    service = AuditService(db)
    logs, total = service.get_logs_for_project(project_id, limit=limit, offset=offset)
    return AuditLogListResponse(logs=logs, total=total)


@router.get("/values/{value_id}", response_model=list[AuditLogResponse])
def get_audit_logs_for_value(
    value_id: int,
    limit: int = Query(default=50, le=100),
    db: Session = Depends(get_db)
):
    """Get audit logs for a specific extracted value."""
    service = AuditService(db)
    return service.get_logs_for_value(value_id, limit=limit)


@router.get("/recent", response_model=list[AuditLogResponse])
def get_recent_activity(
    limit: int = Query(default=50, le=100),
    db: Session = Depends(get_db)
):
    """Get recent activity across all projects."""
    service = AuditService(db)
    return service.get_recent_activity(limit=limit)

