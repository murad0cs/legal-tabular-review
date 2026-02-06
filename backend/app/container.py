"""Dependency Injection Container for service management."""
from typing import Type, TypeVar, Callable, Any, Optional
from sqlalchemy.orm import Session

T = TypeVar('T')


class Container:
    """Simple dependency injection container."""
    
    _instance: Optional['Container'] = None
    _registry: dict[Type, Callable] = {}
    _singletons: dict[Type, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._registry = {}
            cls._instance._singletons = {}
        return cls._instance
    
    def register(
        self,
        interface: Type[T],
        factory: Callable[..., T],
        singleton: bool = False
    ) -> None:
        """Register a service with its factory function."""
        self._registry[interface] = (factory, singleton)
    
    def resolve(self, interface: Type[T], **kwargs) -> T:
        """Resolve a service by its interface."""
        if interface not in self._registry:
            raise ValueError(f"No registration found for {interface}")
        
        factory, is_singleton = self._registry[interface]
        
        if is_singleton:
            if interface not in self._singletons:
                self._singletons[interface] = factory(**kwargs)
            return self._singletons[interface]
        
        return factory(**kwargs)
    
    def clear(self) -> None:
        """Clear all registrations and singletons."""
        self._registry.clear()
        self._singletons.clear()


# Global container instance
container = Container()


def register_services():
    """Register all application services."""
    from .services.extraction_service import ExtractionService
    from .services.ai_extraction_service import AIExtractionService
    from .services.document_service import DocumentService
    from .services.template_service import TemplateService
    from .services.project_service import ProjectService
    from .services.export_service import ExportService
    from .services.audit_service import AuditService
    from .services.validation_service import ValidationService
    from .services.search_service import SearchService
    from .services.settings_service import SettingsService
    from .services.comment_service import CommentService
    from .services.evaluation_service import EvaluationService
    
    # Register services with their factories
    container.register(ExtractionService, lambda db: ExtractionService(db))
    container.register(AIExtractionService, lambda db: AIExtractionService(db))
    container.register(DocumentService, lambda db: DocumentService(db))
    container.register(TemplateService, lambda db: TemplateService(db))
    container.register(ProjectService, lambda db: ProjectService(db))
    container.register(ExportService, lambda db: ExportService(db))
    container.register(AuditService, lambda db: AuditService(db))
    container.register(ValidationService, lambda db: ValidationService(db))
    container.register(SearchService, lambda db: SearchService(db))
    container.register(SettingsService, lambda db: SettingsService(db))
    container.register(CommentService, lambda db: CommentService(db))
    container.register(EvaluationService, lambda db: EvaluationService(db))


def get_service(service_class: Type[T], db: Session) -> T:
    """Helper to get a service instance with database session."""
    return container.resolve(service_class, db=db)


