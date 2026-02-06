"""Base extraction strategy implementing the Strategy Pattern."""
from abc import ABC, abstractmethod
from typing import Any, Optional
from dataclasses import dataclass


@dataclass
class ExtractionResult:
    """Represents a single extraction result."""
    field_name: str
    value: Optional[str]
    citation: Optional[str]
    citation_text: Optional[str]
    confidence: float
    metadata: dict = None
    
    def __post_init__(self):
        self.metadata = self.metadata or {}


class BaseExtractionStrategy(ABC):
    """Base class for extraction strategies following Open/Closed Principle."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Strategy identifier."""
        pass
    
    @property
    @abstractmethod
    def priority(self) -> int:
        """Higher priority strategies are tried first."""
        pass
    
    @abstractmethod
    def can_extract(self, document_type: str, content: str) -> bool:
        """Check if this strategy can handle the given document."""
        pass
    
    @abstractmethod
    def extract(
        self,
        content: str,
        fields: list[dict],
        **kwargs
    ) -> list[ExtractionResult]:
        """Extract field values from document content."""
        pass
    
    def preprocess_content(self, content: str) -> str:
        """Optional preprocessing step."""
        return content.strip()
    
    def postprocess_results(
        self,
        results: list[ExtractionResult]
    ) -> list[ExtractionResult]:
        """Optional postprocessing step."""
        return results


