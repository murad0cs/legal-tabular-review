from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any


class ValidationError(BaseModel):
    """A single validation error."""
    rule: str
    message: str


class ExtractedValueResponse(BaseModel):
    id: int
    document_id: int
    template_field_id: int
    project_id: int
    field_name: Optional[str]
    field_label: Optional[str]
    raw_value: Optional[str]
    normalized_value: Optional[str]
    confidence: float
    citation: Optional[str]
    citation_text: Optional[str]
    status: str
    reviewed_by: Optional[str]
    reviewed_at: Optional[datetime]
    validation_errors: Optional[list[dict[str, Any]]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExtractedValueUpdate(BaseModel):
    raw_value: Optional[str] = None
    status: Optional[str] = None
    reviewer: Optional[str] = None


class ExtractedValuesResponse(BaseModel):
    values: list[ExtractedValueResponse]
    validation_summary: Optional[dict[str, int]] = None  # {"valid": 10, "invalid": 2}

