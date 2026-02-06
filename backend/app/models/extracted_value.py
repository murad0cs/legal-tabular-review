from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from ..database import Base


class ExtractedValue(Base):
    __tablename__ = "extracted_values"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    template_field_id = Column(Integer, ForeignKey("template_fields.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    
    raw_value = Column(Text, nullable=True)
    normalized_value = Column(Text, nullable=True)
    confidence = Column(Float, default=0.0)
    
    citation = Column(Text, nullable=True)
    citation_text = Column(Text, nullable=True)
    
    status = Column(String(50), default="pending")
    reviewed_by = Column(String(255), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    
    # Validation errors as JSON array: [{"rule": "pattern", "message": "Value does not match expected format"}]
    validation_errors = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    document = relationship("Document", back_populates="extracted_values")
    template_field = relationship("TemplateField", back_populates="extracted_values")
    comments = relationship("Comment", back_populates="extracted_value", cascade="all, delete-orphan")

    @property
    def field_name(self) -> str | None:
        return self.template_field.field_name if self.template_field else None

    @property
    def field_label(self) -> str | None:
        return self.template_field.field_label if self.template_field else None
