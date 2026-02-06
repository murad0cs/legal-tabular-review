from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, Any

from ..models.audit_log import AuditLog


class AuditService:
    """Service for tracking all changes made to entities."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def log(
        self,
        entity_type: str,
        entity_id: int,
        action: str,
        user: str = "user",
        old_value: Optional[Any] = None,
        new_value: Optional[Any] = None,
        description: Optional[str] = None,
        project_id: Optional[int] = None,
        document_id: Optional[int] = None
    ) -> AuditLog:
        """Create an audit log entry."""
        log_entry = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            user=user,
            action=action,
            old_value=old_value,
            new_value=new_value,
            description=description,
            project_id=project_id,
            document_id=document_id,
            created_at=datetime.utcnow()
        )
        self.db.add(log_entry)
        self.db.commit()
        self.db.refresh(log_entry)
        return log_entry
    
    def log_value_change(
        self,
        value_id: int,
        action: str,
        user: str = "user",
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        project_id: Optional[int] = None,
        document_id: Optional[int] = None
    ) -> AuditLog:
        """Log a change to an extracted value."""
        return self.log(
            entity_type="extracted_value",
            entity_id=value_id,
            action=action,
            user=user,
            old_value={"value": old_value} if old_value else None,
            new_value={"value": new_value} if new_value else None,
            project_id=project_id,
            document_id=document_id
        )
    
    def log_status_change(
        self,
        value_id: int,
        old_status: str,
        new_status: str,
        user: str = "user",
        project_id: Optional[int] = None,
        document_id: Optional[int] = None
    ) -> AuditLog:
        """Log a status change on an extracted value."""
        return self.log(
            entity_type="extracted_value",
            entity_id=value_id,
            action="status_change",
            user=user,
            old_value={"status": old_status},
            new_value={"status": new_status},
            description=f"Status changed from {old_status} to {new_status}",
            project_id=project_id,
            document_id=document_id
        )
    
    def log_comment(
        self,
        value_id: int,
        comment_id: int,
        action: str,
        user: str = "user",
        content: Optional[str] = None,
        project_id: Optional[int] = None
    ) -> AuditLog:
        """Log a comment action."""
        return self.log(
            entity_type="comment",
            entity_id=comment_id,
            action=action,
            user=user,
            new_value={"content": content, "value_id": value_id} if content else None,
            project_id=project_id
        )
    
    def get_logs_for_project(
        self,
        project_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[list[AuditLog], int]:
        """Get audit logs for a project."""
        query = self.db.query(AuditLog).filter(AuditLog.project_id == project_id)
        total = query.count()
        logs = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
        return logs, total
    
    def get_logs_for_value(
        self,
        value_id: int,
        limit: int = 50
    ) -> list[AuditLog]:
        """Get audit logs for a specific extracted value."""
        return self.db.query(AuditLog).filter(
            AuditLog.entity_type == "extracted_value",
            AuditLog.entity_id == value_id
        ).order_by(AuditLog.created_at.desc()).limit(limit).all()
    
    def get_recent_activity(self, limit: int = 50) -> list[AuditLog]:
        """Get recent activity across all projects."""
        return self.db.query(AuditLog).order_by(
            AuditLog.created_at.desc()
        ).limit(limit).all()

