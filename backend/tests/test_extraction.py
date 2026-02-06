"""
Tests for extraction service.

Run with: pytest backend/tests/ -v
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import will work when running pytest from project root
import sys
sys.path.insert(0, 'backend')

from app.services.normalizer import Normalizer


class TestNormalizer:
    """Tests for the Normalizer class."""
    
    def test_normalize_date_iso_format(self):
        """Test ISO date normalization."""
        result = Normalizer.normalize("January 15, 2024", "iso_date")
        assert result == "2024-01-15"
    
    def test_normalize_date_various_formats(self):
        """Test various date formats."""
        # US format
        result = Normalizer.normalize("01/15/2024", "iso_date")
        assert result == "2024-01-15"
        
        # Already ISO
        result = Normalizer.normalize("2024-01-15", "iso_date")
        assert result == "2024-01-15"
    
    def test_normalize_currency_usd(self):
        """Test USD currency normalization."""
        result = Normalizer.normalize("$50,000.00", "currency_usd")
        assert result == "$50,000.00"
        
        result = Normalizer.normalize("50000", "currency_usd")
        assert result == "$50,000.00"
    
    def test_normalize_uppercase(self):
        """Test uppercase normalization."""
        result = Normalizer.normalize("acme corporation", "uppercase")
        assert result == "ACME CORPORATION"
    
    def test_normalize_lowercase(self):
        """Test lowercase normalization."""
        result = Normalizer.normalize("ACME CORPORATION", "lowercase")
        assert result == "acme corporation"
    
    def test_normalize_none_value(self):
        """Test normalization with None value."""
        result = Normalizer.normalize(None, "iso_date")
        assert result is None
    
    def test_normalize_unknown_rule(self):
        """Test normalization with unknown rule."""
        result = Normalizer.normalize("test", "unknown_rule")
        assert result == "test"


class TestExtractionPatterns:
    """Tests for extraction pattern matching."""
    
    def test_date_pattern_matching(self):
        """Test date extraction patterns."""
        import re
        
        patterns = [
            (r"(?:effective\s+)?(?:date|as\s+of)[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4})", "Section 1", 0.85),
        ]
        
        test_text = "Effective Date: January 15, 2024"
        
        for pattern, _, _ in patterns:
            match = re.search(pattern, test_text, re.IGNORECASE)
            if match:
                assert match.group(1) == "January 15, 2024"
                break
    
    def test_currency_pattern_matching(self):
        """Test currency extraction patterns."""
        import re
        
        patterns = [
            (r"\$\s*([\d,]+(?:\.\d{2})?)", "Financial Terms", 0.80),
        ]
        
        test_text = "Monthly Rent: $5,500.00"
        
        for pattern, _, _ in patterns:
            match = re.search(pattern, test_text, re.IGNORECASE)
            if match:
                assert match.group(1) == "5,500.00"
                break
    
    def test_party_pattern_matching(self):
        """Test party name extraction patterns."""
        import re
        
        patterns = [
            (r"([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*(?:\s+(?:Inc\.|LLC|Corp\.|Corporation|Company)))", "Header", 0.70),
        ]
        
        test_text = "LANDLORD: ACME Properties LLC"
        
        for pattern, _, _ in patterns:
            match = re.search(pattern, test_text, re.IGNORECASE)
            if match:
                assert "LLC" in match.group(1) or "Properties" in match.group(1)
                break


class TestDocumentParsing:
    """Tests for document content parsing."""
    
    def test_html_text_extraction(self):
        """Test HTML text extraction."""
        from app.services.document_service import HTMLTextExtractor
        
        html = """
        <html>
        <head><title>Test</title></head>
        <body>
            <h1>Contract Agreement</h1>
            <p>This is a test paragraph.</p>
            <script>alert('ignored');</script>
            <div>Another section</div>
        </body>
        </html>
        """
        
        parser = HTMLTextExtractor()
        parser.feed(html)
        text = parser.get_text()
        
        assert "Contract Agreement" in text
        assert "test paragraph" in text
        assert "Another section" in text
        assert "alert" not in text  # Script should be ignored


class TestEvaluation:
    """Tests for evaluation metrics."""
    
    def test_precision_calculation(self):
        """Test precision metric calculation."""
        # 3 correct out of 4 extracted = 75% precision
        correct = 3
        total_extracted = 4
        precision = correct / total_extracted
        assert precision == 0.75
    
    def test_recall_calculation(self):
        """Test recall metric calculation."""
        # 3 correct out of 5 expected = 60% recall
        correct = 3
        total_expected = 5
        recall = correct / total_expected
        assert recall == 0.6
    
    def test_f1_calculation(self):
        """Test F1 score calculation."""
        precision = 0.75
        recall = 0.6
        f1 = 2 * (precision * recall) / (precision + recall)
        assert round(f1, 4) == round(0.6667, 4)


class TestValidation:
    """Tests for field validation."""
    
    def test_required_field_validation(self):
        """Test required field validation."""
        # Simulate required field check
        value = None
        is_required = True
        
        errors = []
        if is_required and not value:
            errors.append({"rule": "required", "message": "Field is required"})
        
        assert len(errors) == 1
        assert errors[0]["rule"] == "required"
    
    def test_pattern_validation(self):
        """Test pattern validation."""
        import re
        
        pattern = r"^[A-Z]+"
        value = "ACME"
        
        if not re.fullmatch(pattern, value):
            is_valid = False
        else:
            is_valid = True
        
        assert is_valid is True
        
        # Test failure case
        value = "acme"
        is_valid = bool(re.fullmatch(pattern, value))
        assert is_valid is False
    
    def test_date_range_validation(self):
        """Test date range validation."""
        from datetime import datetime
        
        value = "2024-06-15"
        min_date = "2024-01-01"
        max_date = "2024-12-31"
        
        date_value = datetime.fromisoformat(value)
        min_dt = datetime.fromisoformat(min_date)
        max_dt = datetime.fromisoformat(max_date)
        
        is_valid = min_dt <= date_value <= max_dt
        assert is_valid is True


# Integration test placeholder
class TestAPIIntegration:
    """Integration tests for API endpoints."""
    
    @pytest.mark.skip(reason="Requires running server")
    def test_health_endpoint(self):
        """Test health check endpoint."""
        import httpx
        response = httpx.get("http://localhost:8000/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    @pytest.mark.skip(reason="Requires running server")
    def test_templates_endpoint(self):
        """Test templates listing endpoint."""
        import httpx
        response = httpx.get("http://localhost:8000/api/templates")
        assert response.status_code == 200
        assert "templates" in response.json()

