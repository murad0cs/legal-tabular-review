from .documents import router as documents_router
from .templates import router as templates_router
from .projects import router as projects_router
from .exports import router as exports_router
from .comments import router as comments_router
from .audit import router as audit_router
from .settings import router as settings_router
from .validation import router as validation_router
from .search import router as search_router
from .evaluation import router as evaluation_router

__all__ = [
    "documents_router",
    "templates_router",
    "projects_router",
    "exports_router",
    "comments_router",
    "audit_router",
    "settings_router",
    "validation_router",
    "search_router",
    "evaluation_router"
]
