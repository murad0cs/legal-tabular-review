"""AI-based extraction strategy using OpenAI."""
import json
import logging
import hashlib
from typing import Optional, Any

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .base import BaseExtractionStrategy, ExtractionResult
from ...config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AIExtractionStrategy(BaseExtractionStrategy):
    """AI-powered extraction using OpenAI GPT models."""
    
    SYSTEM_PROMPT = """You are an expert legal document analyst. Extract information precisely and accurately.

Rules:
- Extract EXACT text as it appears in the document
- Provide specific citations (page, paragraph, section)
- Rate confidence based on clarity and context
- Use null for missing/unclear values
- Never invent or assume information"""
    
    EXTRACTION_TEMPLATE = """Extract the following fields from the legal document.

For each field, provide:
1. value: The extracted text (exact match from document)
2. citation: Location reference (e.g., "Section 2.1", "Page 1, Paragraph 3")
3. citation_text: The exact surrounding text (50-100 chars)
4. confidence: Score from 0.0 to 1.0

Fields to extract:
{fields_json}

Document content:
---
{document_content}
---

Return a valid JSON object:
{{"extractions": [{{"field_name": "...", "value": "...", "citation": "...", "citation_text": "...", "confidence": 0.95}}, ...]}}

For any field not found, return: {{"field_name": "...", "value": null, "citation": "Not found", "citation_text": null, "confidence": 0.0}}"""
    
    def __init__(self, api_key: Optional[str] = None):
        self._client = None
        self._api_key = api_key or settings.openai_api_key
        self._cache: dict[str, list[dict]] = {}
    
    @property
    def client(self) -> Optional[OpenAI]:
        if self._client is None and self._api_key:
            self._client = OpenAI(api_key=self._api_key)
        return self._client
    
    @property
    def name(self) -> str:
        return "ai"
    
    @property
    def priority(self) -> int:
        return 100  # High priority
    
    def can_extract(self, document_type: str, content: str) -> bool:
        return (
            self.client is not None and
            content and
            len(content.strip()) > 0
        )
    
    def extract(
        self,
        content: str,
        fields: list[dict],
        use_cache: bool = True,
        **kwargs
    ) -> list[ExtractionResult]:
        content = self.preprocess_content(content)
        
        # Check cache
        cache_key = self._get_cache_key(content, fields)
        if use_cache and cache_key in self._cache:
            logger.info("Using cached AI extraction")
            return self._dict_to_results(self._cache[cache_key])
        
        # Call AI
        try:
            extractions = self._call_ai(content, fields)
            calibrated = self._calibrate_confidence(extractions, fields)
            
            # Cache results
            self._cache[cache_key] = calibrated
            self._cleanup_cache()
            
            return self._dict_to_results(calibrated)
        except Exception as e:
            logger.error(f"AI extraction failed: {e}")
            raise
    
    def _get_cache_key(self, content: str, fields: list[dict]) -> str:
        field_hash = hashlib.md5(
            json.dumps([f.get("field_name") for f in fields], sort_keys=True).encode()
        ).hexdigest()
        content_hash = hashlib.md5(content[:10000].encode()).hexdigest()
        return f"{content_hash}:{field_hash}"
    
    def _cleanup_cache(self, max_size: int = 1000):
        if len(self._cache) > max_size:
            keys = list(self._cache.keys())[:100]
            for key in keys:
                del self._cache[key]
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def _call_ai(self, content: str, fields: list[dict]) -> list[dict]:
        if not self.client:
            raise RuntimeError("OpenAI client not configured")
        
        max_content = 12000
        truncated = content[:max_content]
        if len(content) > max_content:
            truncated += "\n\n[Document truncated...]"
        
        prompt = self.EXTRACTION_TEMPLATE.format(
            fields_json=json.dumps(fields, indent=2),
            document_content=truncated
        )
        
        response = self.client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
            max_tokens=4000
        )
        
        result = json.loads(response.choices[0].message.content)
        return result.get("extractions", [])
    
    def _calibrate_confidence(
        self,
        extractions: list[dict],
        fields: list[dict]
    ) -> list[dict]:
        field_types = {f.get("field_name"): f.get("field_type", "text") for f in fields}
        
        for ext in extractions:
            original = ext.get("confidence", 0.0)
            value = ext.get("value")
            field_type = field_types.get(ext.get("field_name"), "text")
            
            if value is None:
                ext["confidence"] = 0.0
                continue
            
            adjustments = []
            
            # Penalty for short party names
            if field_type == "party" and len(str(value)) < 3:
                adjustments.append(-0.2)
            
            # Penalty for missing citation
            if not ext.get("citation_text"):
                adjustments.append(-0.1)
            
            # Bonus for valid formats
            if field_type == "date" and self._looks_like_date(value):
                adjustments.append(0.05)
            elif field_type == "currency" and self._looks_like_currency(value):
                adjustments.append(0.05)
            
            ext["confidence"] = max(0.0, min(0.95, original + sum(adjustments)))
        
        return extractions
    
    def _looks_like_date(self, value: str) -> bool:
        import re
        patterns = [r'\d{4}-\d{2}-\d{2}', r'\d{1,2}/\d{1,2}/\d{4}', r'[A-Za-z]+\s+\d{1,2},?\s+\d{4}']
        return any(re.search(p, str(value)) for p in patterns)
    
    def _looks_like_currency(self, value: str) -> bool:
        import re
        return bool(re.search(r'[\$\u20ac\xa3]\s*[\d,]+(?:\.\d{2})?', str(value)))
    
    def _dict_to_results(self, extractions: list[dict]) -> list[ExtractionResult]:
        return [
            ExtractionResult(
                field_name=ext.get("field_name", ""),
                value=ext.get("value"),
                citation=ext.get("citation"),
                citation_text=ext.get("citation_text"),
                confidence=ext.get("confidence", 0.0),
                metadata={"strategy": self.name}
            )
            for ext in extractions
        ]

