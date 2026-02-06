import re
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from ..models import ExtractedValue, TemplateField


class ValidationService:
    """Service for validating extracted values against field rules."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def validate_value(self, value: ExtractedValue) -> list[dict]:
        """Validate an extracted value against its field's validation rules.
        
        Returns a list of validation errors (empty if valid).
        """
        errors = []
        
        if not value.template_field:
            return errors
        
        field = value.template_field
        rules = field.validation_rules or {}
        raw_value = value.normalized_value or value.raw_value
        
        # Check required
        if field.is_required and not raw_value:
            errors.append({
                "rule": "required",
                "message": f"{field.field_label} is required but has no value"
            })
            return errors  # No point checking other rules if missing
        
        if not raw_value:
            return errors  # No value to validate
        
        # Validate based on field type
        field_type = field.field_type.lower()
        
        if field_type == "date":
            errors.extend(self._validate_date(raw_value, rules, field.field_label))
        elif field_type == "currency":
            errors.extend(self._validate_currency(raw_value, rules, field.field_label))
        elif field_type in ("number", "integer"):
            errors.extend(self._validate_number(raw_value, rules, field.field_label))
        
        # Check regex pattern (applies to all types)
        if "pattern" in rules:
            if not re.match(rules["pattern"], raw_value):
                errors.append({
                    "rule": "pattern",
                    "message": f"{field.field_label} does not match expected format"
                })
        
        # Check min/max length for text
        if "min_length" in rules and len(raw_value) < rules["min_length"]:
            errors.append({
                "rule": "min_length",
                "message": f"{field.field_label} must be at least {rules['min_length']} characters"
            })
        
        if "max_length" in rules and len(raw_value) > rules["max_length"]:
            errors.append({
                "rule": "max_length",
                "message": f"{field.field_label} must be at most {rules['max_length']} characters"
            })
        
        return errors
    
    def _validate_date(self, value: str, rules: dict, label: str) -> list[dict]:
        """Validate a date value."""
        errors = []
        
        # Try to parse the date
        parsed_date = None
        for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%B %d, %Y", "%b %d, %Y"]:
            try:
                parsed_date = datetime.strptime(value, fmt)
                break
            except ValueError:
                continue
        
        if not parsed_date:
            errors.append({
                "rule": "date_format",
                "message": f"{label} is not a valid date format"
            })
            return errors
        
        # Check date range
        if "min_date" in rules:
            try:
                min_date = datetime.strptime(rules["min_date"], "%Y-%m-%d")
                if parsed_date < min_date:
                    errors.append({
                        "rule": "min_date",
                        "message": f"{label} must be on or after {rules['min_date']}"
                    })
            except ValueError:
                pass
        
        if "max_date" in rules:
            try:
                max_date = datetime.strptime(rules["max_date"], "%Y-%m-%d")
                if parsed_date > max_date:
                    errors.append({
                        "rule": "max_date",
                        "message": f"{label} must be on or before {rules['max_date']}"
                    })
            except ValueError:
                pass
        
        return errors
    
    def _validate_currency(self, value: str, rules: dict, label: str) -> list[dict]:
        """Validate a currency value."""
        errors = []
        
        # Extract numeric value
        numeric_str = re.sub(r'[^\d.-]', '', value)
        
        try:
            amount = float(numeric_str)
        except ValueError:
            errors.append({
                "rule": "currency_format",
                "message": f"{label} is not a valid currency amount"
            })
            return errors
        
        # Check range
        if "min" in rules and amount < rules["min"]:
            errors.append({
                "rule": "min",
                "message": f"{label} must be at least {rules['min']}"
            })
        
        if "max" in rules and amount > rules["max"]:
            errors.append({
                "rule": "max",
                "message": f"{label} must be at most {rules['max']}"
            })
        
        if rules.get("positive_only", False) and amount < 0:
            errors.append({
                "rule": "positive_only",
                "message": f"{label} must be a positive amount"
            })
        
        return errors
    
    def _validate_number(self, value: str, rules: dict, label: str) -> list[dict]:
        """Validate a numeric value."""
        errors = []
        
        try:
            num = float(value.replace(",", ""))
        except ValueError:
            errors.append({
                "rule": "number_format",
                "message": f"{label} is not a valid number"
            })
            return errors
        
        if "min" in rules and num < rules["min"]:
            errors.append({
                "rule": "min",
                "message": f"{label} must be at least {rules['min']}"
            })
        
        if "max" in rules and num > rules["max"]:
            errors.append({
                "rule": "max",
                "message": f"{label} must be at most {rules['max']}"
            })
        
        return errors
    
    def validate_project_values(self, project_id: int) -> dict:
        """Validate all values in a project and update their validation_errors field.
        
        Returns a summary of validation results.
        """
        values = self.db.query(ExtractedValue).filter(
            ExtractedValue.project_id == project_id
        ).all()
        
        total = 0
        valid = 0
        invalid = 0
        
        for value in values:
            errors = self.validate_value(value)
            value.validation_errors = errors if errors else None
            
            total += 1
            if errors:
                invalid += 1
            else:
                valid += 1
        
        self.db.commit()
        
        return {
            "total": total,
            "valid": valid,
            "invalid": invalid
        }
    
    def get_validation_summary(self, project_id: int) -> dict:
        """Get validation summary for a project without re-validating."""
        values = self.db.query(ExtractedValue).filter(
            ExtractedValue.project_id == project_id
        ).all()
        
        total = len(values)
        invalid = sum(1 for v in values if v.validation_errors)
        
        return {
            "total": total,
            "valid": total - invalid,
            "invalid": invalid,
            "errors": [
                {
                    "value_id": v.id,
                    "field": v.field_label,
                    "errors": v.validation_errors
                }
                for v in values if v.validation_errors
            ]
        }

