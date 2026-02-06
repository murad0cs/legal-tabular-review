"""Repository pattern for data access - follows DIP and SRP."""
from .base import BaseRepository
from .document_repository import DocumentRepository
from .project_repository import ProjectRepository
from .template_repository import TemplateRepository
from .extracted_value_repository import ExtractedValueRepository

__all__ = [
    "BaseRepository",
    "DocumentRepository",
    "ProjectRepository",
    "TemplateRepository",
    "ExtractedValueRepository",
]

