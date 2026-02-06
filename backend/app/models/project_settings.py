from sqlalchemy import Column, Integer, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from ..database import Base


class ProjectSettings(Base):
    """Project-specific settings including auto-approve thresholds."""
    __tablename__ = "project_settings"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, unique=True)
    
    # Auto-approve settings
    auto_approve_enabled = Column(Boolean, default=False)
    auto_approve_threshold = Column(Float, default=0.9)  # 90% confidence
    
    # Notification settings
    notify_on_extraction_complete = Column(Boolean, default=False)
    notify_on_low_confidence = Column(Boolean, default=False)
    low_confidence_threshold = Column(Float, default=0.5)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    project = relationship("Project", back_populates="settings")

