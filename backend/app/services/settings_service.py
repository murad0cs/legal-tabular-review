from sqlalchemy.orm import Session
from typing import Optional

from ..models.project_settings import ProjectSettings
from ..models.project import Project


class SettingsService:
    """Service for managing project settings."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_or_create_settings(self, project_id: int) -> ProjectSettings:
        """Get or create settings for a project."""
        settings = self.db.query(ProjectSettings).filter(
            ProjectSettings.project_id == project_id
        ).first()
        
        if not settings:
            # Verify project exists
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise ValueError(f"Project {project_id} not found")
            
            settings = ProjectSettings(project_id=project_id)
            self.db.add(settings)
            self.db.commit()
            self.db.refresh(settings)
        
        return settings
    
    def update_settings(
        self,
        project_id: int,
        auto_approve_enabled: Optional[bool] = None,
        auto_approve_threshold: Optional[float] = None,
        notify_on_extraction_complete: Optional[bool] = None,
        notify_on_low_confidence: Optional[bool] = None,
        low_confidence_threshold: Optional[float] = None
    ) -> ProjectSettings:
        """Update project settings."""
        settings = self.get_or_create_settings(project_id)
        
        if auto_approve_enabled is not None:
            settings.auto_approve_enabled = auto_approve_enabled
        if auto_approve_threshold is not None:
            settings.auto_approve_threshold = auto_approve_threshold
        if notify_on_extraction_complete is not None:
            settings.notify_on_extraction_complete = notify_on_extraction_complete
        if notify_on_low_confidence is not None:
            settings.notify_on_low_confidence = notify_on_low_confidence
        if low_confidence_threshold is not None:
            settings.low_confidence_threshold = low_confidence_threshold
        
        self.db.commit()
        self.db.refresh(settings)
        return settings
    
    def should_auto_approve(self, project_id: int, confidence: float) -> bool:
        """Check if a value should be auto-approved based on settings."""
        settings = self.db.query(ProjectSettings).filter(
            ProjectSettings.project_id == project_id
        ).first()
        
        if not settings or not settings.auto_approve_enabled:
            return False
        
        return confidence >= settings.auto_approve_threshold
    
    def is_low_confidence(self, project_id: int, confidence: float) -> bool:
        """Check if a value is below the low confidence threshold."""
        settings = self.db.query(ProjectSettings).filter(
            ProjectSettings.project_id == project_id
        ).first()
        
        if not settings:
            return confidence < 0.5  # Default threshold
        
        return confidence < settings.low_confidence_threshold


