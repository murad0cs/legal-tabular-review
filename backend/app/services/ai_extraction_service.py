import json
import re
import logging
import hashlib
from datetime import datetime
from typing import Optional, Any

from sqlalchemy.orm import Session
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..models import Document, Template, TemplateField, ExtractedValue, ProjectSettings
from ..config import get_settings
from ..exceptions import ExtractionError
from .normalizer import Normalizer
from .audit_service import AuditService

logger = logging.getLogger(__name__)
settings = get_settings()

PROMPT_TEMPLATES = {
    "v1.0": {
        "system": """You are an expert legal document analyst. Extract information precisely and accurately.
        
Rules:
- Extract EXACT text as it appears in the document
- Provide specific citations (page, paragraph, section)
- Rate confidence based on clarity and context
- Use null for missing/unclear values
- Never invent or assume information""",
        
        "extraction": """Extract the following fields from the legal document.

For each field, provide:
1. value: The extracted text (exact match from document)
2. citation: Location reference (e.g., "Section 2.1", "Page 1, Paragraph 3")
3. citation_text: The exact surrounding text (50-100 chars)
4. confidence: Score from 0.0 to 1.0 based on:
   - 0.9-1.0: Clear, unambiguous match
   - 0.7-0.9: Good match with minor ambiguity
   - 0.5-0.7: Partial match, needs review
   - 0.0-0.5: Low confidence, likely wrong or missing

Fields to extract:
{fields_json}

Document content:
---
{document_content}
---

Return a valid JSON object with this exact structure:
{{"extractions": [
  {{"field_name": "...", "value": "...", "citation": "...", "citation_text": "...", "confidence": 0.95}},
  ...
]}}

Important: For any field not found in the document, return:
{{"field_name": "...", "value": null, "citation": "Not found", "citation_text": null, "confidence": 0.0}}"""
    }
}


class AIExtractionService:
    def __init__(self, db: Session):
        self.db = db
        self.client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
        self.audit_service = AuditService(db)
        self._extraction_cache: dict[str, Any] = {}
        self.prompt_version = "v1.0"
    
    def _get_cache_key(self, document_content: str, fields: list[TemplateField]) -> str:
        field_hash = hashlib.md5(
            json.dumps([f.field_name for f in fields], sort_keys=True).encode()
        ).hexdigest()
        content_hash = hashlib.md5(document_content[:10000].encode()).hexdigest()
        return f"{content_hash}:{field_hash}:{self.prompt_version}"
    
    def _get_cached_extraction(self, cache_key: str) -> Optional[list[dict]]:
        return self._extraction_cache.get(cache_key)
    
    def _cache_extraction(self, cache_key: str, results: list[dict]) -> None:
        if len(self._extraction_cache) > 1000:
            oldest_keys = list(self._extraction_cache.keys())[:100]
            for key in oldest_keys:
                del self._extraction_cache[key]
        self._extraction_cache[cache_key] = results
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True
    )
    def _call_openai(self, messages: list[dict], temperature: float = 0.1) -> dict:
        if not self.client:
            raise ExtractionError("OpenAI client not configured")
        
        response = self.client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            temperature=temperature,
            response_format={"type": "json_object"},
            max_tokens=4000
        )
        
        return json.loads(response.choices[0].message.content)
    
    def extract_fields(
        self,
        document: Document,
        template: Template,
        project_id: int,
        use_cache: bool = True
    ) -> list[ExtractedValue]:
        content = document.content or ""
        if not content.strip():
            logger.warning(f"Document {document.id} has no content")
            return self._create_empty_extractions(document, template, project_id)
        
        # Check cache
        cache_key = self._get_cache_key(content, template.fields)
        if use_cache:
            cached = self._get_cached_extraction(cache_key)
            if cached:
                logger.info(f"Using cached extraction for document {document.id}")
                return self._process_extractions(cached, document, template, project_id)
        
        # Prepare fields schema for prompt
        fields_schema = [
            {
                "field_name": f.field_name,
                "field_label": f.field_label,
                "field_type": f.field_type,
                "description": f.description or f"Extract the {f.field_label}",
                "is_required": f.is_required,
                "example_values": self._get_example_values(f.field_type)
            }
            for f in template.fields
        ]
        
        # Try AI extraction
        if self.client:
            try:
                extractions = self._extract_with_ai(content, fields_schema)
                self._cache_extraction(cache_key, extractions)
                return self._process_extractions(extractions, document, template, project_id)
            except Exception as e:
                logger.error(f"AI extraction failed: {e}, falling back to patterns")
        
        # Fallback to pattern matching
        return self._extract_with_patterns(document, template, project_id)
    
    def _get_example_values(self, field_type: str) -> list[str]:
        examples = {
            "party": ["ACME Corporation", "John Smith LLC", "Global Services Inc."],
            "date": ["January 15, 2024", "2024-01-15", "15/01/2024"],
            "currency": ["$50,000.00", "USD 100,000", "$1,500/month"],
            "text": ["Standard confidentiality terms", "Mutual agreement"],
            "clause": ["Either party may terminate with 30 days notice..."]
        }
        return examples.get(field_type, [])
    
    def _extract_with_ai(self, content: str, fields_schema: list[dict]) -> list[dict]:
        prompts = PROMPT_TEMPLATES[self.prompt_version]
        max_content_length = 12000
        truncated_content = content[:max_content_length]
        if len(content) > max_content_length:
            truncated_content += "\n\n[Document truncated...]"
        
        user_prompt = prompts["extraction"].format(
            fields_json=json.dumps(fields_schema, indent=2),
            document_content=truncated_content
        )
        
        messages = [
            {"role": "system", "content": prompts["system"]},
            {"role": "user", "content": user_prompt}
        ]
        
        result = self._call_openai(messages)
        extractions = result.get("extractions", [])
        
        calibrated = self._calibrate_confidence(extractions, fields_schema)
        return calibrated
    
    def _calibrate_confidence(
        self,
        extractions: list[dict],
        fields_schema: list[dict]
    ) -> list[dict]:
        field_types = {f["field_name"]: f["field_type"] for f in fields_schema}
        
        for ext in extractions:
            original_conf = ext.get("confidence", 0.0)
            value = ext.get("value")
            field_type = field_types.get(ext.get("field_name"), "text")
            
            if value is None:
                ext["confidence"] = 0.0
                continue
            
            adjustments = []
            
            if field_type == "party" and len(str(value)) < 3:
                adjustments.append(-0.2)
            
            if not ext.get("citation_text"):
                adjustments.append(-0.1)
            
            if field_type == "date" and self._looks_like_date(value):
                adjustments.append(0.05)
            elif field_type == "currency" and self._looks_like_currency(value):
                adjustments.append(0.05)
            
            adjusted = original_conf + sum(adjustments)
            ext["confidence"] = max(0.0, min(0.95, adjusted))
        
        return extractions
    
    def _looks_like_date(self, value: str) -> bool:
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',
            r'\d{1,2}/\d{1,2}/\d{4}',
            r'[A-Za-z]+\s+\d{1,2},?\s+\d{4}'
        ]
        return any(re.search(p, str(value)) for p in date_patterns)
    
    def _looks_like_currency(self, value: str) -> bool:
        return bool(re.search(r'[\$\u20ac\xa3]\s*[\d,]+(?:\.\d{2})?', str(value)))
    
    def _process_extractions(
        self,
        extractions: list[dict],
        document: Document,
        template: Template,
        project_id: int
    ) -> list[ExtractedValue]:
        field_map = {f.field_name: f for f in template.fields}
        values = []
        
        proj_settings = self.db.query(ProjectSettings).filter(
            ProjectSettings.project_id == project_id
        ).first()
        auto_approve = proj_settings.auto_approve_enabled if proj_settings else False
        threshold = proj_settings.auto_approve_threshold if proj_settings else 0.9
        
        for ext in extractions:
            field = field_map.get(ext.get("field_name"))
            if not field:
                continue
            
            raw_value = ext.get("value")
            normalized_value = Normalizer.normalize(raw_value, field.normalization_rule)
            confidence = ext.get("confidence", 0.0)
            status = "pending"
            reviewer = None
            reviewed_at = None
            if auto_approve and confidence >= threshold:
                status = "approved"
                reviewer = "auto"
                reviewed_at = datetime.utcnow()
            
            ev = ExtractedValue(
                document_id=document.id,
                template_field_id=field.id,
                project_id=project_id,
                raw_value=raw_value,
                normalized_value=normalized_value,
                confidence=confidence,
                citation=ext.get("citation"),
                citation_text=ext.get("citation_text"),
                status=status,
                reviewed_by=reviewer,
                reviewed_at=reviewed_at
            )
            self.db.add(ev)
            values.append(ev)
        
        self.db.commit()
        
        for ev in values:
            self.audit_service.log(
                entity_type="extracted_value",
                entity_id=ev.id,
                action="ai_extracted" if ev.status == "pending" else "ai_auto_approved",
                user="ai_system",
                new_value={"value": ev.raw_value, "confidence": ev.confidence},
                project_id=project_id,
                document_id=document.id
            )
        
        return values
    
    def _create_empty_extractions(
        self,
        document: Document,
        template: Template,
        project_id: int
    ) -> list[ExtractedValue]:
        values = []
        for field in template.fields:
            ev = ExtractedValue(
                document_id=document.id,
                template_field_id=field.id,
                project_id=project_id,
                raw_value=None,
                normalized_value=None,
                confidence=0.0,
                citation="Document empty",
                citation_text=None,
                status="pending"
            )
            self.db.add(ev)
            values.append(ev)
        self.db.commit()
        return values
    
    def _extract_with_patterns(
        self,
        document: Document,
        template: Template,
        project_id: int
    ) -> list[ExtractedValue]:
        from .extraction_service import ExtractionService
        basic_service = ExtractionService(self.db)
        return basic_service._extract_with_patterns(document, template, project_id)
    
    def batch_extract(
        self,
        documents: list[Document],
        template: Template,
        project_id: int
    ) -> list[ExtractedValue]:
        all_values = []
        for doc in documents:
            if doc.status != "ready" or not doc.content:
                continue
            
            self.db.query(ExtractedValue).filter(
                ExtractedValue.document_id == doc.id,
                ExtractedValue.project_id == project_id
            ).delete()
            
            values = self.extract_fields(doc, template, project_id)
            all_values.extend(values)
        
        return all_values
    
    def get_extraction_stats(self, project_id: int) -> dict:
        values = self.db.query(ExtractedValue).filter(
            ExtractedValue.project_id == project_id
        ).all()
        
        if not values:
            return {"total": 0, "avg_confidence": 0, "by_status": {}}
        
        confidences = [v.confidence for v in values]
        statuses = {}
        for v in values:
            statuses[v.status] = statuses.get(v.status, 0) + 1
        
        return {
            "total": len(values),
            "avg_confidence": sum(confidences) / len(confidences),
            "min_confidence": min(confidences),
            "max_confidence": max(confidences),
            "by_status": statuses,
            "high_confidence_count": sum(1 for c in confidences if c >= 0.8),
            "low_confidence_count": sum(1 for c in confidences if c < 0.5)
        }

