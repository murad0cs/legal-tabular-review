from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any


class AuditLogResponse(BaseModel):
    id: int
    entity_type: str
    entity_id: int
    user: str
    action: str
    old_value: Optional[Any]
    new_value: Optional[Any]
    description: Optional[str]
    project_id: Optional[int]
    document_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    logs: list[AuditLogResponse]
    total: int

