"""Template repository with template-specific queries."""
from typing import Optional
from sqlalchemy.orm import Session, joinedload

from .base import BaseRepository
from ..models import Template, TemplateField


class TemplateRepository(BaseRepository[Template]):
    """Repository for Template entity operations."""
    
    def __init__(self, db: Session):
        super().__init__(db, Template)
    
    def get_by_name(self, name: str) -> Optional[Template]:
        """Get template by name."""
        return self.db.query(Template).filter(Template.name == name).first()
    
    def get_with_fields(self, id: int) -> Optional[Template]:
        """Get template with fields eagerly loaded."""
        return self.db.query(Template).options(
            joinedload(Template.fields)
        ).filter(Template.id == id).first()
    
    def get_all_with_fields(self, skip: int = 0, limit: int = 100) -> list[Template]:
        """Get all templates with fields eagerly loaded."""
        return self.db.query(Template).options(
            joinedload(Template.fields)
        ).offset(skip).limit(limit).all()
    
    def add_field(self, template_id: int, field: TemplateField) -> TemplateField:
        """Add a field to a template."""
        field.template_id = template_id
        self.db.add(field)
        self.db.flush()
        return field
    
    def get_field(self, template_id: int, field_id: int) -> Optional[TemplateField]:
        """Get a specific field from a template."""
        return self.db.query(TemplateField).filter(
            TemplateField.template_id == template_id,
            TemplateField.id == field_id
        ).first()
    
    def update_field(self, field_id: int, data: dict) -> Optional[TemplateField]:
        """Update a template field."""
        field = self.db.query(TemplateField).filter(
            TemplateField.id == field_id
        ).first()
        
        if field:
            for key, value in data.items():
                if hasattr(field, key):
                    setattr(field, key, value)
            self.db.flush()
        
        return field
    
    def delete_field(self, field_id: int) -> bool:
        """Delete a template field."""
        deleted = self.db.query(TemplateField).filter(
            TemplateField.id == field_id
        ).delete()
        self.db.flush()
        return deleted > 0
    
    def reorder_fields(self, template_id: int, field_ids: list[int]) -> bool:
        """Reorder template fields."""
        for order, field_id in enumerate(field_ids):
            self.db.query(TemplateField).filter(
                TemplateField.id == field_id,
                TemplateField.template_id == template_id
            ).update({"display_order": order})
        self.db.flush()
        return True

