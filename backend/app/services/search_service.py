from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import Optional

from ..models import ExtractedValue, Document, Project, TemplateField


class SearchService:
    """Service for searching across all extracted values."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def search(
        self,
        query: str,
        project_id: Optional[int] = None,
        field_type: Optional[str] = None,
        status: Optional[str] = None,
        min_confidence: Optional[float] = None,
        max_confidence: Optional[float] = None,
        limit: int = 100,
        offset: int = 0
    ) -> dict:
        """Search extracted values across all projects.
        
        Args:
            query: Text to search for in raw_value, normalized_value, or citation_text
            project_id: Optional filter by project
            field_type: Optional filter by field type (date, currency, party, etc.)
            status: Optional filter by status (pending, approved, rejected)
            min_confidence: Optional minimum confidence threshold
            max_confidence: Optional maximum confidence threshold
            limit: Maximum results to return
            offset: Offset for pagination
        
        Returns:
            Dictionary with results and metadata
        """
        # Build base query with joins
        base_query = self.db.query(ExtractedValue).join(
            TemplateField, ExtractedValue.template_field_id == TemplateField.id
        ).join(
            Document, ExtractedValue.document_id == Document.id
        ).join(
            Project, ExtractedValue.project_id == Project.id
        )
        
        # Text search across multiple fields
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
        
        # Apply filters
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
        
        # Get total count
        total = base_query.count()
        
        # Apply pagination and get results
        results = base_query.order_by(
            ExtractedValue.confidence.desc()
        ).offset(offset).limit(limit).all()
        
        # Format results with context
        formatted = []
        for value in results:
            formatted.append({
                "id": value.id,
                "raw_value": value.raw_value,
                "normalized_value": value.normalized_value,
                "confidence": value.confidence,
                "status": value.status,
                "citation": value.citation,
                "citation_text": value.citation_text,
                "validation_errors": value.validation_errors,
                "field": {
                    "id": value.template_field.id,
                    "name": value.template_field.field_name,
                    "label": value.template_field.field_label,
                    "type": value.template_field.field_type
                },
                "document": {
                    "id": value.document.id,
                    "filename": value.document.original_filename
                },
                "project": {
                    "id": value.document.project_documents[0].project.id if value.document.project_documents else None,
                    "name": value.document.project_documents[0].project.name if value.document.project_documents else None
                }
            })
        
        return {
            "results": formatted,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(results) < total
        }
    
    def get_field_types(self) -> list[str]:
        """Get all distinct field types used in templates."""
        types = self.db.query(TemplateField.field_type).distinct().all()
        return [t[0] for t in types]
    
    def get_search_suggestions(self, query: str, limit: int = 10) -> list[dict]:
        """Get search suggestions based on existing values."""
        if not query or len(query) < 2:
            return []
        
        search_term = f"%{query}%"
        
        # Get distinct normalized values that match
        values = self.db.query(
            ExtractedValue.normalized_value,
            TemplateField.field_label
        ).join(
            TemplateField, ExtractedValue.template_field_id == TemplateField.id
        ).filter(
            ExtractedValue.normalized_value.ilike(search_term)
        ).distinct().limit(limit).all()
        
        return [
            {"value": v[0], "field": v[1]}
            for v in values if v[0]
        ]

