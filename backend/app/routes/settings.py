from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.settings_service import SettingsService
from ..schemas import ProjectSettingsUpdate, ProjectSettingsResponse

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/projects/{project_id}", response_model=ProjectSettingsResponse)
def get_project_settings(
    project_id: int,
    db: Session = Depends(get_db)
):
    """Get settings for a project. Creates default settings if none exist."""
    service = SettingsService(db)
    try:
        settings = service.get_or_create_settings(project_id)
        return settings
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/projects/{project_id}", response_model=ProjectSettingsResponse)
def update_project_settings(
    project_id: int,
    data: ProjectSettingsUpdate,
    db: Session = Depends(get_db)
):
    """Update settings for a project."""
    service = SettingsService(db)
    try:
        settings = service.update_settings(
            project_id=project_id,
            auto_approve_enabled=data.auto_approve_enabled,
            auto_approve_threshold=data.auto_approve_threshold,
            notify_on_extraction_complete=data.notify_on_extraction_complete,
            notify_on_low_confidence=data.notify_on_low_confidence,
            low_confidence_threshold=data.low_confidence_threshold
        )
        return settings
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

