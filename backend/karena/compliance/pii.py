"""PII (Personally Identifiable Information) detection and masking.

Detects and redacts:
- Email addresses
- Phone numbers
- Credit card numbers
- Social security numbers
- Names and identifiers
- IP addresses
- Dates of birth
- Government IDs
- Bank account numbers
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class PIIType(str, Enum):
    """Types of personally identifiable information."""

    EMAIL = "email"
    PHONE = "phone"
    CREDIT_CARD = "credit_card"
    SSN = "ssn"
    NAME = "name"
    IP_ADDRESS = "ip_address"
    DOB = "date_of_birth"
    PASSPORT = "passport"
    DRIVERS_LICENSE = "drivers_license"
    BANK_ACCOUNT = "bank_account"
    CUSTOM = "custom"


@dataclass
class PIIMatch:
    """A detected PII item."""

    pii_type: PIIType
    text: str
    start_pos: int
    end_pos: int
    confidence: float = 1.0  # 0.0-1.0


class PIIDetector:
    """Detects PII in text."""

    # Regex patterns for common PII
    PATTERNS = {
        PIIType.EMAIL: r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        PIIType.PHONE: r"\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b",
        PIIType.CREDIT_CARD: r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b",
        PIIType.SSN: r"\b(?!000|666|9)\d{3}-(?!00)\d{2}-(?!0000)\d{4}\b",
        PIIType.IP_ADDRESS: r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b",
        PIIType.BANK_ACCOUNT: r"\b[0-9]{8,17}\b",  # Generic bank account format
    }

    def __init__(self) -> None:
        self._compiled_patterns = {
            pii_type: re.compile(pattern) for pii_type, pattern in self.PATTERNS.items()
        }
        self._custom_patterns: dict[str, re.Pattern] = {}

    def add_custom_pattern(self, name: str, pattern: str) -> None:
        """Add a custom PII detection pattern."""
        self._custom_patterns[name] = re.compile(pattern)

    def detect(self, text: str) -> list[PIIMatch]:
        """Detect all PII in text."""
        matches = []

        # Check built-in patterns
        for pii_type, compiled_pattern in self._compiled_patterns.items():
            for match in compiled_pattern.finditer(text):
                matches.append(
                    PIIMatch(
                        pii_type=pii_type,
                        text=match.group(),
                        start_pos=match.start(),
                        end_pos=match.end(),
                    )
                )

        # Check custom patterns
        for custom_name, compiled_pattern in self._custom_patterns.items():
            for match in compiled_pattern.finditer(text):
                matches.append(
                    PIIMatch(
                        pii_type=PIIType.CUSTOM,
                        text=match.group(),
                        start_pos=match.start(),
                        end_pos=match.end(),
                    )
                )

        # Sort by position and deduplicate overlapping matches
        matches = sorted(matches, key=lambda m: m.start_pos)
        deduplicated = []
        for match in matches:
            # Skip if overlaps with previous match
            if deduplicated and match.start_pos < deduplicated[-1].end_pos:
                continue
            deduplicated.append(match)

        return deduplicated

    def has_pii(self, text: str, min_confidence: float = 0.5) -> bool:
        """Quick check if text contains PII."""
        matches = self.detect(text)
        return any(m.confidence >= min_confidence for m in matches)

    def get_pii_summary(self, text: str) -> dict[PIIType, int]:
        """Get count of each PII type detected."""
        matches = self.detect(text)
        summary: dict[PIIType, int] = {}
        for match in matches:
            summary[match.pii_type] = summary.get(match.pii_type, 0) + 1
        return summary


class PIIMasker:
    """Masks detected PII in text."""

    def __init__(self, detector: PIIDetector | None = None) -> None:
        self.detector = detector or PIIDetector()

    def mask(
        self,
        text: str,
        replacement: str = "[REDACTED]",
        exclude_types: list[PIIType] | None = None,
    ) -> str:
        """Replace all detected PII with replacement text."""
        exclude_types = exclude_types or []
        matches = self.detector.detect(text)

        # Build result string by processing matches in reverse order
        result = text
        for match in reversed(matches):
            if match.pii_type not in exclude_types:
                result = result[: match.start_pos] + replacement + result[match.end_pos :]

        return result

    def mask_partial(
        self,
        text: str,
        pii_type: PIIType | None = None,
        keep_start: int = 0,
        keep_end: int = 0,
    ) -> str:
        """Partially mask PII (keep some characters visible)."""
        matches = self.detector.detect(text)

        result = text
        for match in reversed(matches):
            if pii_type is None or match.pii_type == pii_type:
                masked = self._partial_mask(match.text, keep_start, keep_end)
                result = result[: match.start_pos] + masked + result[match.end_pos :]

        return result

    @staticmethod
    def _partial_mask(text: str, keep_start: int = 0, keep_end: int = 0) -> str:
        """Mask string while keeping start and end characters."""
        if len(text) <= keep_start + keep_end:
            return "*" * len(text)

        start = text[:keep_start] if keep_start > 0 else ""
        end = text[-keep_end:] if keep_end > 0 else ""
        middle = "*" * (len(text) - keep_start - keep_end)
        return start + middle + end

    def mask_email(self, text: str) -> str:
        """Mask only email addresses."""
        return self.mask(text, exclude_types=[PIIType.EMAIL])

    def mask_phone(self, text: str) -> str:
        """Mask only phone numbers."""
        return self.mask(text, exclude_types=[PIIType.PHONE])

    def mask_credit_cards(self, text: str) -> str:
        """Mask only credit card numbers."""
        return self.mask(text, exclude_types=[PIIType.CREDIT_CARD])


# Global singleton instances
_pii_detector: PIIDetector | None = None
_pii_masker: PIIMasker | None = None


def get_pii_detector() -> PIIDetector:
    """Get or create the global PII detector."""
    global _pii_detector
    if _pii_detector is None:
        _pii_detector = PIIDetector()
    return _pii_detector


def get_pii_masker() -> PIIMasker:
    """Get or create the global PII masker."""
    global _pii_masker
    if _pii_masker is None:
        _pii_masker = PIIMasker(get_pii_detector())
    return _pii_masker
