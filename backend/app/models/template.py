from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from ..database import Base


class Template(Base):
    __tablename__ = "templates"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    document_type = Column(String(100), nullable=False)
    version = Column(Integer, default=1)  # For template versioning
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    fields = relationship(
        "TemplateField",
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="TemplateField.order_index"
    )
    projects = relationship("Project", back_populates="template")


class TemplateField(Base):
    __tablename__ = "template_fields"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    template_id = Column(Integer, ForeignKey("templates.id"), nullable=False)
    field_name = Column(String(255), nullable=False)
    field_label = Column(String(255), nullable=False)
    field_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    normalization_rule = Column(String(100), nullable=True)
    is_required = Column(Boolean, default=False)
    order_index = Column(Integer, default=0)
    
    # Validation rules as JSON: {"pattern": "regex", "min": 0, "max": 100, "min_date": "2020-01-01", "max_date": "2030-12-31"}
    validation_rules = Column(JSON, nullable=True)
    
    template = relationship("Template", back_populates="fields")
    extracted_values = relationship(
        "ExtractedValue",
        back_populates="template_field",
        cascade="all, delete-orphan"
    )
