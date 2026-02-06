from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from ..database import Base


class Comment(Base):
    """Comments/notes on extracted values for review discussion."""
    __tablename__ = "comments"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    extracted_value_id = Column(Integer, ForeignKey("extracted_values.id"), nullable=False)
    
    author = Column(String(255), nullable=False, default="user")
    content = Column(Text, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    extracted_value = relationship("ExtractedValue", back_populates="comments")

