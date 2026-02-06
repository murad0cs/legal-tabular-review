"""Document repository with document-specific queries."""
from typing import Optional
from sqlalchemy.orm import Session

from .base import BaseRepository
from ..models import Document


class DocumentRepository(BaseRepository[Document]):
    """Repository for Document entity operations."""
    
    def __init__(self, db: Session):
        super().__init__(db, Document)
    
    def get_by_filename(self, filename: str) -> Optional[Document]:
        """Get document by original filename."""
        return self.db.query(Document).filter(
            Document.original_filename == filename
        ).first()
    
    def get_ready_documents(self, skip: int = 0, limit: int = 100) -> list[Document]:
        """Get documents that are ready for processing."""
        return self.db.query(Document).filter(
            Document.status == "ready"
        ).offset(skip).limit(limit).all()
    
    def get_by_status(self, status: str, skip: int = 0, limit: int = 100) -> list[Document]:
        """Get documents by status."""
        return self.db.query(Document).filter(
            Document.status == status
        ).offset(skip).limit(limit).all()
    
    def update_status(self, id: int, status: str, error_message: str = None) -> Optional[Document]:
        """Update document status."""
        doc = self.get_by_id(id)
        if doc:
            doc.status = status
            if error_message:
                doc.error_message = error_message
            self.db.flush()
        return doc
    
    def get_documents_for_project(self, project_id: int) -> list[Document]:
        """Get all documents associated with a project."""
        from ..models import ProjectDocument
        return self.db.query(Document).join(
            ProjectDocument, Document.id == ProjectDocument.document_id
        ).filter(
            ProjectDocument.project_id == project_id
        ).all()


