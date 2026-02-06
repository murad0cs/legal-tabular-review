from pydantic import BaseModel, Field
from typing import Optional


class ProjectSettingsCreate(BaseModel):
    auto_approve_enabled: bool = False
    auto_approve_threshold: float = Field(default=0.9, ge=0.0, le=1.0)
    notify_on_extraction_complete: bool = False
    notify_on_low_confidence: bool = False
    low_confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)


class ProjectSettingsUpdate(BaseModel):
    auto_approve_enabled: Optional[bool] = None
    auto_approve_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    notify_on_extraction_complete: Optional[bool] = None
    notify_on_low_confidence: Optional[bool] = None
    low_confidence_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)


class ProjectSettingsResponse(BaseModel):
    id: int
    project_id: int
    auto_approve_enabled: bool
    auto_approve_threshold: float
    notify_on_extraction_complete: bool
    notify_on_low_confidence: bool
    low_confidence_threshold: float

    class Config:
        from_attributes = True


