from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from ..database import Base


class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    template_id = Column(Integer, ForeignKey("templates.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String(50), default="draft")
    
    template = relationship("Template", back_populates="projects")
    project_documents = relationship(
        "ProjectDocument",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    settings = relationship(
        "ProjectSettings",
        back_populates="project",
        uselist=False,
        cascade="all, delete-orphan"
    )

    @property
    def document_count(self) -> int:
        return len(self.project_documents)


class ProjectDocument(Base):
    __tablename__ = "project_documents"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)
    
    project = relationship("Project", back_populates="project_documents")
    document = relationship("Document", back_populates="project_documents")
