"""Abstract interfaces for dependency injection and extensibility."""
from abc import ABC, abstractmethod
from typing import Any, Optional


class IExtractionStrategy(ABC):
    """Interface for extraction strategies (AI, Pattern, etc.)"""
    
    @abstractmethod
    def extract(
        self,
        content: str,
        fields: list[dict],
        **kwargs
    ) -> list[dict]:
        """Extract field values from document content."""
        pass
    
    @abstractmethod
    def supports(self, document_type: str) -> bool:
        """Check if this strategy supports the document type."""
        pass


class INormalizer(ABC):
    """Interface for value normalization."""
    
    @abstractmethod
    def normalize(self, value: Any, rule: str) -> Any:
        """Normalize a value according to a rule."""
        pass
    
    @abstractmethod
    def supports_rule(self, rule: str) -> bool:
        """Check if this normalizer supports the rule."""
        pass


class IRepository(ABC):
    """Base repository interface for data access."""
    
    @abstractmethod
    def get_by_id(self, id: int) -> Optional[Any]:
        pass
    
    @abstractmethod
    def get_all(self, **filters) -> list[Any]:
        pass
    
    @abstractmethod
    def create(self, entity: Any) -> Any:
        pass
    
    @abstractmethod
    def update(self, id: int, data: dict) -> Any:
        pass
    
    @abstractmethod
    def delete(self, id: int) -> bool:
        pass


class IEventPublisher(ABC):
    """Interface for event publishing (for future async processing)."""
    
    @abstractmethod
    def publish(self, event_type: str, payload: dict) -> None:
        pass


class ICacheProvider(ABC):
    """Interface for caching."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        pass
    
    @abstractmethod
    def delete(self, key: str) -> None:
        pass
    
    @abstractmethod
    def clear(self) -> None:
        pass


