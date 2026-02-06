from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Any


# Validation rules schema
class ValidationRules(BaseModel):
    """Validation rules for a template field."""
    pattern: Optional[str] = None  # Regex pattern for validation
    min: Optional[float] = None  # Minimum value (for numbers/currency)
    max: Optional[float] = None  # Maximum value (for numbers/currency)
    min_date: Optional[str] = None  # Minimum date (YYYY-MM-DD)
    max_date: Optional[str] = None  # Maximum date (YYYY-MM-DD)
    min_length: Optional[int] = None  # Minimum text length
    max_length: Optional[int] = None  # Maximum text length
    positive_only: Optional[bool] = None  # For currency/numbers


class FieldBase(BaseModel):
    field_name: str = Field(..., min_length=1, max_length=255)
    field_label: str = Field(..., min_length=1, max_length=255)
    field_type: str = Field(..., pattern="^(text|date|currency|party|clause|number)$")
    description: Optional[str] = None
    normalization_rule: Optional[str] = None
    is_required: bool = False
    validation_rules: Optional[dict[str, Any]] = None


class FieldCreate(FieldBase):
    pass


class FieldUpdate(BaseModel):
    field_name: Optional[str] = Field(None, min_length=1, max_length=255)
    field_label: Optional[str] = Field(None, min_length=1, max_length=255)
    field_type: Optional[str] = Field(None, pattern="^(text|date|currency|party|clause|number)$")
    description: Optional[str] = None
    normalization_rule: Optional[str] = None
    is_required: Optional[bool] = None
    order_index: Optional[int] = None
    validation_rules: Optional[dict[str, Any]] = None


class FieldResponse(BaseModel):
    id: int
    template_id: int
    field_name: str
    field_label: str
    field_type: str
    description: Optional[str]
    normalization_rule: Optional[str]
    is_required: bool
    order_index: int
    validation_rules: Optional[dict[str, Any]] = None

    class Config:
        from_attributes = True


class FieldReorderRequest(BaseModel):
    field_ids: list[int]


class TemplateBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    document_type: str = Field(..., min_length=1, max_length=100)


class TemplateCreate(TemplateBase):
    pass


class TemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    document_type: Optional[str] = Field(None, min_length=1, max_length=100)


class TemplateResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    document_type: str
    version: int = 1
    created_at: datetime
    updated_at: datetime
    fields: list[FieldResponse] = []

    class Config:
        from_attributes = True


class TemplateExport(BaseModel):
    """Schema for template import/export."""
    name: str
    description: Optional[str]
    document_type: str
    fields: list[FieldCreate]


class TemplateListResponse(BaseModel):
    templates: list[TemplateResponse]

