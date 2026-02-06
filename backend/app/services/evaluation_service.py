import logging
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime

from ..models import ExtractedValue, Project
from ..exceptions import NotFoundError

logger = logging.getLogger(__name__)


class EvaluationService:
    def __init__(self, db: Session):
        self.db = db
    
    def evaluate_project(
        self,
        project_id: int,
        ground_truth: dict[str, dict[str, str]]
    ) -> dict:
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise NotFoundError("Project", project_id)
        
        values = self.db.query(ExtractedValue).filter(
            ExtractedValue.project_id == project_id
        ).all()
        
        extracted_map = {}
        for v in values:
            doc_name = v.document.original_filename if v.document else str(v.document_id)
            field_name = v.template_field.field_name if v.template_field else str(v.template_field_id)
            
            if doc_name not in extracted_map:
                extracted_map[doc_name] = {}
            extracted_map[doc_name][field_name] = {
                "raw_value": v.raw_value,
                "normalized_value": v.normalized_value,
                "confidence": v.confidence
            }
        
        results = {
            "project_id": project_id,
            "evaluated_at": datetime.utcnow().isoformat(),
            "documents": [],
            "summary": {
                "total_fields": 0,
                "correct_extractions": 0,
                "incorrect_extractions": 0,
                "missing_extractions": 0,
                "precision": 0.0,
                "recall": 0.0,
                "f1_score": 0.0,
                "avg_confidence_correct": 0.0,
                "avg_confidence_incorrect": 0.0
            }
        }
        
        correct_confidences = []
        incorrect_confidences = []
        
        for doc_name, expected_fields in ground_truth.items():
            doc_result = {
                "document": doc_name,
                "fields": [],
                "correct": 0,
                "incorrect": 0,
                "missing": 0
            }
            
            extracted_fields = extracted_map.get(doc_name, {})
            
            for field_name, expected_value in expected_fields.items():
                results["summary"]["total_fields"] += 1
                
                extracted = extracted_fields.get(field_name, {})
                actual_value = extracted.get("normalized_value") or extracted.get("raw_value")
                confidence = extracted.get("confidence", 0.0)
                
                is_match = self._compare_values(actual_value, expected_value)
                
                field_result = {
                    "field_name": field_name,
                    "expected": expected_value,
                    "extracted": actual_value,
                    "confidence": confidence,
                    "is_correct": is_match,
                    "status": "correct" if is_match else ("missing" if actual_value is None else "incorrect")
                }
                doc_result["fields"].append(field_result)
                
                if is_match:
                    doc_result["correct"] += 1
                    results["summary"]["correct_extractions"] += 1
                    correct_confidences.append(confidence)
                elif actual_value is None:
                    doc_result["missing"] += 1
                    results["summary"]["missing_extractions"] += 1
                else:
                    doc_result["incorrect"] += 1
                    results["summary"]["incorrect_extractions"] += 1
                    incorrect_confidences.append(confidence)
            
            results["documents"].append(doc_result)
        
        total = results["summary"]["total_fields"]
        correct = results["summary"]["correct_extractions"]
        extracted_count = correct + results["summary"]["incorrect_extractions"]
        
        if extracted_count > 0:
            results["summary"]["precision"] = round(correct / extracted_count, 4)
        
        if total > 0:
            results["summary"]["recall"] = round(correct / total, 4)
        
        precision = results["summary"]["precision"]
        recall = results["summary"]["recall"]
        if precision + recall > 0:
            results["summary"]["f1_score"] = round(
                2 * (precision * recall) / (precision + recall), 4
            )
        
        if correct_confidences:
            results["summary"]["avg_confidence_correct"] = round(
                sum(correct_confidences) / len(correct_confidences), 4
            )
        
        if incorrect_confidences:
            results["summary"]["avg_confidence_incorrect"] = round(
                sum(incorrect_confidences) / len(incorrect_confidences), 4
            )
        
        return results
    
    def _compare_values(self, actual: Optional[str], expected: str) -> bool:
        if actual is None:
            return False
        
        actual_norm = self._normalize_for_comparison(actual)
        expected_norm = self._normalize_for_comparison(expected)
        
        if actual_norm == expected_norm:
            return True
        
        if expected_norm in actual_norm:
            return True
        
        if self._are_semantically_equivalent(actual, expected):
            return True
        
        return False
    
    def _normalize_for_comparison(self, value: str) -> str:
        return " ".join(value.lower().split())
    
    def _are_semantically_equivalent(self, actual: str, expected: str) -> bool:
        actual_date = self._parse_date(actual)
        expected_date = self._parse_date(expected)
        if actual_date and expected_date and actual_date == expected_date:
            return True
        
        actual_amount = self._parse_currency(actual)
        expected_amount = self._parse_currency(expected)
        if actual_amount is not None and expected_amount is not None:
            return abs(actual_amount - expected_amount) < 0.01
        
        return False
    
    def _parse_date(self, value: str) -> Optional[str]:
        import re
        from datetime import datetime as dt
        
        patterns = [
            (r'(\d{4})-(\d{2})-(\d{2})', '%Y-%m-%d'),
            (r'(\d{2})/(\d{2})/(\d{4})', '%m/%d/%Y'),
            (r'([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})', None),
        ]
        
        for pattern, fmt in patterns:
            match = re.search(pattern, value)
            if match:
                try:
                    if fmt:
                        parsed = dt.strptime(match.group(0), fmt)
                        return parsed.strftime('%Y-%m-%d')
                except (ValueError, AttributeError):
                    pass
        return None
    
    def _parse_currency(self, value: str) -> Optional[float]:
        import re
        match = re.search(r'[\$€£]?\s*([\d,]+(?:\.\d{2})?)', value)
        if match:
            try:
                return float(match.group(1).replace(',', ''))
            except (ValueError, AttributeError):
                pass
        return None
    
    def get_evaluation_summary(self, project_id: int) -> dict:
        values = self.db.query(ExtractedValue).filter(
            ExtractedValue.project_id == project_id
        ).all()
        
        if not values:
            return {"total": 0, "message": "No extractions found"}
        
        confidences = [v.confidence for v in values]
        statuses = {}
        for v in values:
            statuses[v.status] = statuses.get(v.status, 0) + 1
        
        high_confidence = sum(1 for c in confidences if c >= 0.8)
        medium_confidence = sum(1 for c in confidences if 0.5 <= c < 0.8)
        low_confidence = sum(1 for c in confidences if c < 0.5)
        
        quality_score = (high_confidence * 1.0 + medium_confidence * 0.5) / len(values)
        
        return {
            "project_id": project_id,
            "total_values": len(values),
            "by_status": statuses,
            "confidence_distribution": {
                "high": high_confidence,
                "medium": medium_confidence,
                "low": low_confidence
            },
            "avg_confidence": round(sum(confidences) / len(confidences), 4),
            "quality_score": round(quality_score, 4),
            "quality_rating": (
                "excellent" if quality_score >= 0.8 else
                "good" if quality_score >= 0.6 else
                "fair" if quality_score >= 0.4 else
                "needs_improvement"
            )
        }

