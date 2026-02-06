"""Pattern-based extraction strategy."""
import re
from typing import Optional
from .base import BaseExtractionStrategy, ExtractionResult


class PatternRegistry:
    """Registry for field type patterns - allows runtime extension."""
    
    _patterns: dict[str, list[tuple[str, str, float]]] = {}
    
    @classmethod
    def register(cls, field_type: str, patterns: list[tuple[str, str, float]]):
        """Register patterns for a field type."""
        cls._patterns[field_type] = patterns
    
    @classmethod
    def get_patterns(cls, field_type: str, field_name: str = "") -> list[tuple[str, str, float]]:
        """Get patterns for a field type."""
        if field_type in cls._patterns:
            return cls._patterns[field_type]
        return cls._get_default_patterns(field_type, field_name)
    
    @classmethod
    def _get_default_patterns(cls, field_type: str, field_name: str) -> list[tuple[str, str, float]]:
        """Default patterns when none registered."""
        name_lower = field_name.lower() if field_name else ""
        
        if field_type == "date" or "date" in name_lower:
            return [
                (r"(?:effective\s+)?(?:date|as\s+of)[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4})", "Section 1", 0.85),
                (r"dated[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4})", "Header", 0.80),
                (r"(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})", "Document Body", 0.75),
                (r"([A-Za-z]+\s+\d{1,2},?\s+\d{4})", "Document Body", 0.70),
            ]
        
        if field_type == "party" or "party" in name_lower:
            return [
                (r"(?:between|by\s+and\s+between)[:\s]+([A-Z][A-Za-z\s,\.]+?)(?:\s*\(|,\s*a)", "Preamble", 0.80),
                (r'"([A-Z][A-Za-z\s]+(?:Inc\.|LLC|Corp\.|Corporation|Company)?)"', "Definitions", 0.75),
                (r"([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*(?:\s+(?:Inc\.|LLC|Corp\.|Corporation|Company)))", "Header", 0.70),
            ]
        
        if field_type == "currency" or any(x in name_lower for x in ["value", "amount", "price", "rent", "deposit"]):
            return [
                (r"\$\s*([\d,]+(?:\.\d{2})?)", "Financial Terms", 0.80),
                (r"([\d,]+(?:\.\d{2})?)\s*(?:dollars|USD)", "Financial Terms", 0.75),
                (r"(?:amount|sum|total)[:\s]+\$?\s*([\d,]+(?:\.\d{2})?)", "Payment Section", 0.70),
            ]
        
        if field_type == "clause":
            keywords = field_name.replace("_", "|") if field_name else "clause"
            return [
                (rf"(?:{keywords})[:\s]+([^.]+(?:\.[^.]+){{0,2}})", f"Section: {field_name}", 0.70),
            ]
        
        # Generic text field
        keywords = field_name.replace("_", "|") if field_name else "text"
        return [
            (rf"(?:{keywords})[:\s]+([^\n]+)", "Document Body", 0.65),
        ]


# Register default patterns
PatternRegistry.register("date", [
    (r"(?:effective\s+)?(?:date|as\s+of)[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4})", "Section 1", 0.85),
    (r"dated[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4})", "Header", 0.80),
    (r"(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})", "Document Body", 0.75),
])

PatternRegistry.register("party", [
    (r"(?:between|by\s+and\s+between)[:\s]+([A-Z][A-Za-z\s,\.]+?)(?:\s*\(|,\s*a)", "Preamble", 0.80),
    (r'"([A-Z][A-Za-z\s]+(?:Inc\.|LLC|Corp\.|Corporation|Company)?)"', "Definitions", 0.75),
])

PatternRegistry.register("currency", [
    (r"\$\s*([\d,]+(?:\.\d{2})?)", "Financial Terms", 0.80),
    (r"([\d,]+(?:\.\d{2})?)\s*(?:dollars|USD)", "Financial Terms", 0.75),
])


class PatternExtractionStrategy(BaseExtractionStrategy):
    """Pattern-based extraction using regex."""
    
    @property
    def name(self) -> str:
        return "pattern"
    
    @property
    def priority(self) -> int:
        return 10  # Lower priority than AI
    
    def can_extract(self, document_type: str, content: str) -> bool:
        # Pattern extraction works on any text content
        return bool(content and len(content.strip()) > 0)
    
    def extract(
        self,
        content: str,
        fields: list[dict],
        **kwargs
    ) -> list[ExtractionResult]:
        results = []
        content = self.preprocess_content(content)
        
        for field in fields:
            result = self._extract_field(content, field)
            results.append(result)
        
        return self.postprocess_results(results)
    
    def _extract_field(self, content: str, field: dict) -> ExtractionResult:
        field_type = field.get("field_type", "text")
        field_name = field.get("field_name", "")
        
        patterns = PatternRegistry.get_patterns(field_type, field_name)
        
        for pattern, location, confidence in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                start = max(0, match.start() - 50)
                end = min(len(content), match.end() + 50)
                citation_text = content[start:end].strip()
                
                return ExtractionResult(
                    field_name=field_name,
                    value=value,
                    citation=location,
                    citation_text=citation_text,
                    confidence=confidence,
                    metadata={"strategy": self.name, "pattern": pattern}
                )
        
        return ExtractionResult(
            field_name=field_name,
            value=None,
            citation="Not found",
            citation_text=None,
            confidence=0.0,
            metadata={"strategy": self.name}
        )


