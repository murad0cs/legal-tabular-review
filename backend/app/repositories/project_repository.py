"""Project repository with project-specific queries."""
from typing import Optional
from sqlalchemy.orm import Session

from .base import BaseRepository
from ..models import Project, ProjectDocument


class ProjectRepository(BaseRepository[Project]):
    """Repository for Project entity operations."""
    
    def __init__(self, db: Session):
        super().__init__(db, Project)
    
    def get_by_name(self, name: str) -> Optional[Project]:
        """Get project by name."""
        return self.db.query(Project).filter(Project.name == name).first()
    
    def get_by_status(self, status: str, skip: int = 0, limit: int = 100) -> list[Project]:
        """Get projects by status."""
        return self.db.query(Project).filter(
            Project.status == status
        ).offset(skip).limit(limit).all()
    
    def get_with_template(self, id: int) -> Optional[Project]:
        """Get project with template eagerly loaded."""
        from sqlalchemy.orm import joinedload
        return self.db.query(Project).options(
            joinedload(Project.template)
        ).filter(Project.id == id).first()
    
    def add_document(self, project_id: int, document_id: int) -> bool:
        """Add a document to a project."""
        existing = self.db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.document_id == document_id
        ).first()
        
        if existing:
            return False
        
        pd = ProjectDocument(project_id=project_id, document_id=document_id)
        self.db.add(pd)
        self.db.flush()
        return True
    
    def remove_document(self, project_id: int, document_id: int) -> bool:
        """Remove a document from a project."""
        deleted = self.db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.document_id == document_id
        ).delete()
        self.db.flush()
        return deleted > 0
    
    def get_document_ids(self, project_id: int) -> list[int]:
        """Get all document IDs for a project."""
        results = self.db.query(ProjectDocument.document_id).filter(
            ProjectDocument.project_id == project_id
        ).all()
        return [r[0] for r in results]
    
    def update_status(self, id: int, status: str) -> Optional[Project]:
        """Update project status."""
        project = self.get_by_id(id)
        if project:
            project.status = status
            self.db.flush()
        return project


