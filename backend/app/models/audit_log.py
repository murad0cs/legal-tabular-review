from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from datetime import datetime

from ..database import Base


class AuditLog(Base):
    """Tracks all changes made to extracted values for compliance."""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # What was changed
    entity_type = Column(String(50), nullable=False)  # extracted_value, project, document, etc.
    entity_id = Column(Integer, nullable=False)
    
    # Who made the change
    user = Column(String(255), nullable=False, default="user")
    
    # What action was taken
    action = Column(String(50), nullable=False)  # create, update, approve, reject, comment, etc.
    
    # Details of the change
    old_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    description = Column(Text, nullable=True)
    
    # Context
    project_id = Column(Integer, nullable=True)
    document_id = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)


