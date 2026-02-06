import re
from typing import Callable


class Normalizer:
    """
    Standardizes extracted values into consistent formats.
    Supports dates, currencies, text casing, etc.
    """
    
    MONTHS = {
        "january": "01", "february": "02", "march": "03", "april": "04",
        "may": "05", "june": "06", "july": "07", "august": "08",
        "september": "09", "october": "10", "november": "11", "december": "12",
        "jan": "01", "feb": "02", "mar": "03", "apr": "04",
        "jun": "06", "jul": "07", "aug": "08", "sep": "09",
        "oct": "10", "nov": "11", "dec": "12"
    }
    
    @classmethod
    def normalize(cls, value: str | None, rule: str | None) -> str | None:
        if value is None or not rule:
            return value
        
        normalizers: dict[str, Callable[[str], str]] = {
            "iso_date": cls._normalize_date,
            "uppercase": lambda v: v.upper().strip(),
            "lowercase": lambda v: v.lower().strip(),
            "currency_usd": cls._normalize_currency_usd,
            "currency_eur": cls._normalize_currency_eur,
            "phone": cls._normalize_phone,
            "email": lambda v: v.lower().strip(),
            "percentage": cls._normalize_percentage,
            "trim": lambda v: " ".join(v.split()),
        }
        
        normalizer = normalizers.get(rule.lower())
        return normalizer(value) if normalizer else value
    
    @classmethod
    def _normalize_date(cls, value: str) -> str:
        """Convert various date formats to ISO (YYYY-MM-DD)."""
        patterns = [
            (r"(\w+)\s+(\d{1,2}),?\s+(\d{4})", cls._parse_month_day_year),
            (r"(\d{1,2})\s+(\w+)\s+(\d{4})", cls._parse_day_month_year),
            (r"(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})", lambda m: f"{m.group(3)}-{m.group(1).zfill(2)}-{m.group(2).zfill(2)}"),
            (r"(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})", lambda m: f"{m.group(1)}-{m.group(2).zfill(2)}-{m.group(3).zfill(2)}"),
        ]
        
        for pattern, converter in patterns:
            match = re.search(pattern, value, re.IGNORECASE)
            if match:
                try:
                    return converter(match)
                except (ValueError, KeyError):
                    continue
        return value
    
    @classmethod
    def _parse_month_day_year(cls, match) -> str:
        month = cls.MONTHS.get(match.group(1).lower(), "01")
        return f"{match.group(3)}-{month}-{match.group(2).zfill(2)}"
    
    @classmethod
    def _parse_day_month_year(cls, match) -> str:
        month = cls.MONTHS.get(match.group(2).lower(), "01")
        return f"{match.group(3)}-{month}-{match.group(1).zfill(2)}"
    
    @classmethod
    def _normalize_currency_usd(cls, value: str) -> str:
        """Format as $X,XXX.XX"""
        cleaned = re.sub(r"[^\d.,]", "", value)
        cleaned = cls._parse_number(cleaned)
        try:
            return f"${float(cleaned):,.2f}"
        except ValueError:
            return value
    
    @classmethod
    def _normalize_currency_eur(cls, value: str) -> str:
        """Format as €X.XXX,XX (European style)"""
        cleaned = re.sub(r"[^\d.,]", "", value)
        cleaned = cls._parse_number(cleaned)
        try:
            amount = float(cleaned)
            formatted = f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            return f"€{formatted}"
        except ValueError:
            return value
    
    @classmethod
    def _parse_number(cls, value: str) -> str:
        """Handle both US (1,234.56) and EU (1.234,56) number formats."""
        if "," in value and "." in value:
            # Figure out which is the decimal separator
            if value.rindex(",") > value.rindex("."):
                return value.replace(".", "").replace(",", ".")
            return value.replace(",", "")
        elif "," in value:
            parts = value.split(",")
            if len(parts[-1]) == 2:
                return value.replace(",", ".")
            return value.replace(",", "")
        return value
    
    @classmethod
    def _normalize_phone(cls, value: str) -> str:
        """Format as +1-XXX-XXX-XXXX"""
        digits = re.sub(r"[^\d+]", "", value)
        if len(digits) == 10:
            return f"+1-{digits[:3]}-{digits[3:6]}-{digits[6:]}"
        if len(digits) == 11 and digits.startswith("1"):
            return f"+{digits[0]}-{digits[1:4]}-{digits[4:7]}-{digits[7:]}"
        return value
    
    @classmethod
    def _normalize_percentage(cls, value: str) -> str:
        match = re.search(r"[\d.,]+", value)
        if match:
            try:
                return f"{float(match.group().replace(',', '.')):,.2f}%"
            except ValueError:
                pass
        return value
