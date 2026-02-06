import json
import re
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from openai import OpenAI

from ..models import Project, Document, Template, TemplateField, ExtractedValue, ProjectSettings
from ..config import get_settings
from ..exceptions import NotFoundError, ExtractionError
from .normalizer import Normalizer
from .audit_service import AuditService

logger = logging.getLogger(__name__)
settings = get_settings()


class ExtractionService:
    """Handles field extraction from documents using AI or pattern matching."""
    
    def __init__(self, db: Session):
        self.db = db
        self.client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
        self.audit_service = AuditService(db)
    
    def extract_for_project(self, project_id: int) -> list[ExtractedValue]:
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise NotFoundError("Project", project_id)
        
        if not project.template or not project.template.fields:
            raise ExtractionError("Project has no template or template has no fields")
        
        project.status = "in_progress"
        self.db.commit()
        
        all_values = []
        for pd in project.project_documents:
            if pd.document.status != "ready" or not pd.document.content:
                continue
            
            # Clear previous extractions for this document
            self.db.query(ExtractedValue).filter(
                ExtractedValue.document_id == pd.document.id,
                ExtractedValue.project_id == project_id
            ).delete()
            
            values = self._extract_fields(pd.document, project.template, project_id)
            all_values.extend(values)
        
        project.status = "needs_review"
        self.db.commit()
        return all_values
    
    def _extract_fields(self, document: Document, template: Template, project_id: int) -> list[ExtractedValue]:
        # Use AI if configured, otherwise fall back to pattern matching
        if self.client:
            return self._extract_with_ai(document, template, project_id)
        return self._extract_with_patterns(document, template, project_id)
    
    def _extract_with_ai(self, document: Document, template: Template, project_id: int) -> list[ExtractedValue]:
        fields_schema = [
            {
                "field_name": f.field_name,
                "field_label": f.field_label,
                "field_type": f.field_type,
                "description": f.description or f"Extract the {f.field_label}",
                "is_required": f.is_required
            }
            for f in template.fields
        ]
        
        prompt = f"""Extract the following fields from the legal document.

For each field provide:
1. The extracted value (raw text as it appears)
2. Citation showing location (e.g., "Page 1, Paragraph 3")
3. The exact quoted text supporting the extraction
4. Confidence score from 0.0 to 1.0

Fields:
{json.dumps(fields_schema, indent=2)}

Document:
{document.content[:15000]}

Return JSON:
{{"extractions": [{{"field_name": "...", "value": "...", "citation": "...", "citation_text": "...", "confidence": 0.95}}]}}

For missing fields, use value: null, confidence: 0.0, citation: "Not found"."""
        
        try:
            response = self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "You are a legal document analyst. Extract information precisely."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return self._process_extractions(result.get("extractions", []), document, template, project_id)
            
        except Exception as e:
            logger.error(f"AI extraction failed: {e}")
            return self._extract_with_patterns(document, template, project_id)
    
    def _process_extractions(
        self,
        extractions: list[dict],
        document: Document,
        template: Template,
        project_id: int
    ) -> list[ExtractedValue]:
        field_map = {f.field_name: f for f in template.fields}
        values = []
        
        # Check auto-approve settings
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
            
            # Determine status based on auto-approve
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
        
        # Log extractions
        for ev in values:
            self.audit_service.log(
                entity_type="extracted_value",
                entity_id=ev.id,
                action="extracted" if ev.status == "pending" else "auto_approved",
                user="system",
                new_value={"value": ev.raw_value, "confidence": ev.confidence},
                project_id=project_id,
                document_id=document.id
            )
        
        return values
    
    def _extract_with_patterns(self, document: Document, template: Template, project_id: int) -> list[ExtractedValue]:
        """Fallback extraction using regex patterns when AI is unavailable."""
        content = document.content or ""
        values = []
        
        # Check auto-approve settings
        proj_settings = self.db.query(ProjectSettings).filter(
            ProjectSettings.project_id == project_id
        ).first()
        auto_approve = proj_settings.auto_approve_enabled if proj_settings else False
        threshold = proj_settings.auto_approve_threshold if proj_settings else 0.9
        
        for field in template.fields:
            raw_value, citation, citation_text, confidence = self._pattern_extract(content, field)
            normalized_value = Normalizer.normalize(raw_value, field.normalization_rule)
            
            # Determine status based on auto-approve
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
                citation=citation,
                citation_text=citation_text,
                status=status,
                reviewed_by=reviewer,
                reviewed_at=reviewed_at
            )
            self.db.add(ev)
            values.append(ev)
        
        self.db.commit()
        
        # Log extractions
        for ev in values:
            self.audit_service.log(
                entity_type="extracted_value",
                entity_id=ev.id,
                action="extracted" if ev.status == "pending" else "auto_approved",
                user="system",
                new_value={"value": ev.raw_value, "confidence": ev.confidence},
                project_id=project_id,
                document_id=document.id
            )
        
        return values
    
    def _pattern_extract(self, content: str, field: TemplateField) -> tuple[str | None, str | None, str | None, float]:
        patterns = self._get_patterns_for_field(field)
        
        for pattern, location, confidence in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                # Grab surrounding context for citation
                start = max(0, match.start() - 50)
                end = min(len(content), match.end() + 50)
                citation_text = content[start:end].strip()
                return value, location, citation_text, confidence
        
        return None, "Not found", None, 0.0
    
    def _get_patterns_for_field(self, field: TemplateField) -> list[tuple[str, str, float]]:
        """Build regex patterns based on field type and name."""
        field_type = field.field_type
        field_name = field.field_name.lower()
        
        if field_type == "date" or "date" in field_name:
            return [
                (r"(?:effective\s+)?(?:date|as\s+of)[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4})", "Section 1", 0.85),
                (r"dated[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4})", "Header", 0.80),
                (r"(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})", "Document Body", 0.75),
                (r"([A-Za-z]+\s+\d{1,2},?\s+\d{4})", "Document Body", 0.70),
            ]
        
        if field_type == "party" or "party" in field_name:
            return [
                (r"(?:between|by\s+and\s+between)[:\s]+([A-Z][A-Za-z\s,\.]+?)(?:\s*\(|,\s*a)", "Preamble", 0.80),
                (r'"([A-Z][A-Za-z\s]+(?:Inc\.|LLC|Corp\.|Corporation|Company)?)"', "Definitions", 0.75),
                (r"([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*(?:\s+(?:Inc\.|LLC|Corp\.|Corporation|Company)))", "Header", 0.70),
            ]
        
        if field_type == "currency" or any(x in field_name for x in ["value", "amount", "price", "rent", "deposit"]):
            return [
                (r"\$\s*([\d,]+(?:\.\d{2})?)", "Financial Terms", 0.80),
                (r"([\d,]+(?:\.\d{2})?)\s*(?:dollars|USD)", "Financial Terms", 0.75),
                (r"(?:amount|sum|total)[:\s]+\$?\s*([\d,]+(?:\.\d{2})?)", "Payment Section", 0.70),
            ]
        
        if field_type == "clause":
            keywords = field.field_name.replace("_", "|")
            return [
                (rf"(?:{keywords})[:\s]+([^.]+(?:\.[^.]+){{0,2}})", f"Section: {field.field_label}", 0.70),
            ]
        
        # Generic text field
        keywords = field.field_name.replace("_", "|")
        return [
            (rf"(?:{keywords})[:\s]+([^\n]+)", "Document Body", 0.65),
        ]
    
    def get_project_values(self, project_id: int) -> list[ExtractedValue]:
        return self.db.query(ExtractedValue).filter(ExtractedValue.project_id == project_id).all()
    
    def update_value(
        self,
        value_id: int,
        new_value: str | None = None,
        status: str | None = None,
        reviewer: str | None = None
    ) -> ExtractedValue:
        ev = self.db.query(ExtractedValue).filter(ExtractedValue.id == value_id).first()
        if not ev:
            raise NotFoundError("ExtractedValue", value_id)
        
        old_status = ev.status
        old_value = ev.raw_value
        
        if new_value is not None:
            ev.raw_value = new_value
            if ev.template_field:
                ev.normalized_value = Normalizer.normalize(new_value, ev.template_field.normalization_rule)
            ev.status = "edited"
            
            # Log value change
            self.audit_service.log_value_change(
                value_id=value_id,
                action="value_edited",
                user=reviewer or "user",
                old_value=old_value,
                new_value=new_value,
                project_id=ev.project_id,
                document_id=ev.document_id
            )
        
        if status is not None:
            ev.status = status
            if status != old_status:
                self.audit_service.log_status_change(
                    value_id=value_id,
                    old_status=old_status,
                    new_status=status,
                    user=reviewer or "user",
                    project_id=ev.project_id,
                    document_id=ev.document_id
                )
        
        if reviewer is not None:
            ev.reviewed_by = reviewer
            ev.reviewed_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(ev)
        return ev
    
    def approve_value(self, value_id: int, reviewer: str = "user") -> ExtractedValue:
        return self.update_value(value_id, status="approved", reviewer=reviewer)
    
    def reject_value(self, value_id: int, reviewer: str = "user") -> ExtractedValue:
        return self.update_value(value_id, status="rejected", reviewer=reviewer)
    
    def bulk_approve(self, value_ids: list[int], reviewer: str = "user") -> list[int]:
        """Approve multiple values at once."""
        updated_ids = []
        for value_id in value_ids:
            try:
                ev = self.db.query(ExtractedValue).filter(ExtractedValue.id == value_id).first()
                if ev:
                    old_status = ev.status
                    ev.status = "approved"
                    ev.reviewed_by = reviewer
                    ev.reviewed_at = datetime.utcnow()
                    updated_ids.append(value_id)
                    
                    # Log the change
                    self.audit_service.log_status_change(
                        value_id=value_id,
                        old_status=old_status,
                        new_status="approved",
                        user=reviewer,
                        project_id=ev.project_id,
                        document_id=ev.document_id
                    )
            except Exception as e:
                logger.error(f"Failed to approve value {value_id}: {e}")
        self.db.commit()
        return updated_ids
    
    def bulk_reject(self, value_ids: list[int], reviewer: str = "user") -> list[int]:
        """Reject multiple values at once."""
        updated_ids = []
        for value_id in value_ids:
            try:
                ev = self.db.query(ExtractedValue).filter(ExtractedValue.id == value_id).first()
                if ev:
                    old_status = ev.status
                    ev.status = "rejected"
                    ev.reviewed_by = reviewer
                    ev.reviewed_at = datetime.utcnow()
                    updated_ids.append(value_id)
                    
                    # Log the change
                    self.audit_service.log_status_change(
                        value_id=value_id,
                        old_status=old_status,
                        new_status="rejected",
                        user=reviewer,
                        project_id=ev.project_id,
                        document_id=ev.document_id
                    )
            except Exception as e:
                logger.error(f"Failed to reject value {value_id}: {e}")
        self.db.commit()
        return updated_ids