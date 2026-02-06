from sqlalchemy.orm import Session

from ..models import Project, ProjectDocument, Document
from ..exceptions import NotFoundError


class ProjectService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(self) -> list[Project]:
        return self.db.query(Project).order_by(Project.created_at.desc()).all()
    
    def get_by_id(self, project_id: int) -> Project:
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise NotFoundError("Project", project_id)
        return project
    
    def create(self, name: str, template_id: int, description: str | None = None) -> Project:
        project = Project(name=name, description=description, template_id=template_id, status="draft")
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project
    
    def update(self, project_id: int, **kwargs) -> Project:
        project = self.get_by_id(project_id)
        for key, value in kwargs.items():
            if value is not None and hasattr(project, key):
                setattr(project, key, value)
        self.db.commit()
        self.db.refresh(project)
        return project
    
    def delete(self, project_id: int) -> None:
        project = self.get_by_id(project_id)
        self.db.delete(project)
        self.db.commit()
    
    def add_documents(self, project_id: int, document_ids: list[int]) -> list[ProjectDocument]:
        self.get_by_id(project_id)
        added = []
        
        for doc_id in document_ids:
            doc = self.db.query(Document).filter(Document.id == doc_id).first()
            if not doc:
                continue
            
            existing = self.db.query(ProjectDocument).filter(
                ProjectDocument.project_id == project_id,
                ProjectDocument.document_id == doc_id
            ).first()
            if existing:
                continue
            
            pd = ProjectDocument(project_id=project_id, document_id=doc_id)
            self.db.add(pd)
            added.append(pd)
        
        self.db.commit()
        return added
    
    def remove_document(self, project_id: int, document_id: int) -> None:
        pd = self.db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.document_id == document_id
        ).first()
        
        if not pd:
            raise NotFoundError("ProjectDocument", f"{project_id}-{document_id}")
        
        self.db.delete(pd)
        self.db.commit()
    
    def get_documents(self, project_id: int) -> list[Document]:
        project = self.get_by_id(project_id)
        return [pd.document for pd in project.project_documents]
