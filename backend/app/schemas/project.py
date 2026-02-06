from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

from .document import DocumentResponse
from .template import TemplateResponse


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    template_id: int


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(draft|in_progress|completed|needs_review)$")


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    template_id: int
    created_at: datetime
    updated_at: datetime
    status: str
    document_count: int = 0

    class Config:
        from_attributes = True


class ProjectDetailResponse(ProjectResponse):
    documents: list[DocumentResponse] = []
    template: Optional[TemplateResponse] = None


class ProjectListResponse(BaseModel):
    projects: list[ProjectResponse]


class AddDocumentsRequest(BaseModel):
    document_ids: list[int]


class BulkValueActionRequest(BaseModel):
    value_ids: list[int]


class BulkValueActionResponse(BaseModel):
    message: str
    count: int
    updated_ids: list[int]
