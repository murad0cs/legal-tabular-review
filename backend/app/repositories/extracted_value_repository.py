"""ExtractedValue repository with extraction-specific queries."""
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from .base import BaseRepository
from ..models import ExtractedValue


class ExtractedValueRepository(BaseRepository[ExtractedValue]):
    """Repository for ExtractedValue entity operations."""
    
    def __init__(self, db: Session):
        super().__init__(db, ExtractedValue)
    
    def get_for_project(
        self,
        project_id: int,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 1000
    ) -> list[ExtractedValue]:
        """Get all extracted values for a project."""
        query = self.db.query(ExtractedValue).filter(
            ExtractedValue.project_id == project_id
        )
        
        if status:
            query = query.filter(ExtractedValue.status == status)
        
        return query.offset(skip).limit(limit).all()
    
    def get_for_document(
        self,
        document_id: int,
        project_id: Optional[int] = None
    ) -> list[ExtractedValue]:
        """Get all extracted values for a document."""
        query = self.db.query(ExtractedValue).filter(
            ExtractedValue.document_id == document_id
        )
        
        if project_id:
            query = query.filter(ExtractedValue.project_id == project_id)
        
        return query.all()
    
    def get_for_field(
        self,
        field_id: int,
        project_id: Optional[int] = None
    ) -> list[ExtractedValue]:
        """Get all extracted values for a template field."""
        query = self.db.query(ExtractedValue).filter(
            ExtractedValue.template_field_id == field_id
        )
        
        if project_id:
            query = query.filter(ExtractedValue.project_id == project_id)
        
        return query.all()
    
    def update_status(
        self,
        id: int,
        status: str,
        reviewer: str = "user"
    ) -> Optional[ExtractedValue]:
        """Update the status of an extracted value."""
        value = self.get_by_id(id)
        if value:
            value.status = status
            value.reviewed_by = reviewer
            value.reviewed_at = datetime.utcnow()
            self.db.flush()
        return value
    
    def bulk_update_status(
        self,
        ids: list[int],
        status: str,
        reviewer: str = "user"
    ) -> int:
        """Bulk update status of multiple values."""
        updated = self.db.query(ExtractedValue).filter(
            ExtractedValue.id.in_(ids)
        ).update(
            {
                "status": status,
                "reviewed_by": reviewer,
                "reviewed_at": datetime.utcnow()
            },
            synchronize_session=False
        )
        self.db.flush()
        return updated
    
    def delete_for_document(self, document_id: int, project_id: int) -> int:
        """Delete all extracted values for a document in a project."""
        deleted = self.db.query(ExtractedValue).filter(
            ExtractedValue.document_id == document_id,
            ExtractedValue.project_id == project_id
        ).delete()
        self.db.flush()
        return deleted
    
    def search(
        self,
        query: str,
        project_id: Optional[int] = None,
        field_type: Optional[str] = None,
        status: Optional[str] = None,
        min_confidence: Optional[float] = None,
        max_confidence: Optional[float] = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[list[ExtractedValue], int]:
        """Search extracted values with filters."""
        from ..models import TemplateField, Document
        
        base_query = self.db.query(ExtractedValue).join(
            TemplateField, ExtractedValue.template_field_id == TemplateField.id
        ).join(
            Document, ExtractedValue.document_id == Document.id
        )
        
        if query:
            search_term = f"%{query}%"
            base_query = base_query.filter(
                or_(
                    ExtractedValue.raw_value.ilike(search_term),
                    ExtractedValue.normalized_value.ilike(search_term),
                    ExtractedValue.citation_text.ilike(search_term),
                    TemplateField.field_label.ilike(search_term),
                    Document.original_filename.ilike(search_term)
                )
            )
        
        if project_id:
            base_query = base_query.filter(ExtractedValue.project_id == project_id)
        
        if field_type:
            base_query = base_query.filter(TemplateField.field_type == field_type)
        
        if status:
            base_query = base_query.filter(ExtractedValue.status == status)
        
        if min_confidence is not None:
            base_query = base_query.filter(ExtractedValue.confidence >= min_confidence)
        
        if max_confidence is not None:
            base_query = base_query.filter(ExtractedValue.confidence <= max_confidence)
        
        total = base_query.count()
        results = base_query.order_by(
            ExtractedValue.confidence.desc()
        ).offset(skip).limit(limit).all()
        
        return results, total
    
    def get_statistics(self, project_id: int) -> dict:
        """Get statistics for extracted values in a project."""
        values = self.get_for_project(project_id)
        
        if not values:
            return {
                "total": 0,
                "by_status": {},
                "avg_confidence": 0.0,
                "confidence_distribution": {"high": 0, "medium": 0, "low": 0}
            }
        
        statuses = {}
        confidences = []
        high = medium = low = 0
        
        for v in values:
            statuses[v.status] = statuses.get(v.status, 0) + 1
            confidences.append(v.confidence)
            
            if v.confidence >= 0.8:
                high += 1
            elif v.confidence >= 0.5:
                medium += 1
            else:
                low += 1
        
        return {
            "total": len(values),
            "by_status": statuses,
            "avg_confidence": sum(confidences) / len(confidences),
            "min_confidence": min(confidences),
            "max_confidence": max(confidences),
            "confidence_distribution": {"high": high, "medium": medium, "low": low}
        }


