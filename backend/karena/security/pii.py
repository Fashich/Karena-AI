"""Karena AI Personally Identifiable Information (PII) Detector.

Specialized detector for identifying and handling PII in compliance
with global privacy regulations (GDPR, PDPA, CCPA, etc.).
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PIICategory(str, Enum):
    """Categories of PII data."""
    
    # Personal Identifiers
    NAME = "name"
    EMAIL = "email"
    PHONE = "phone"
    ADDRESS = "address"
    
    # Government IDs
    SSN = "ssn"  # US Social Security Number
    PASSPORT = "passport"
    DRIVERS_LICENSE = "drivers_license"
    TAX_ID = "tax_id"
    
    # Financial
    CREDIT_CARD = "credit_card"
    BANK_ACCOUNT = "bank_account"
    IBAN = "iban"
    
    # Health
    MEDICAL_RECORD = "medical_record"
    HEALTH_INSURANCE = "health_insurance"
    
    # Digital
    IP_ADDRESS = "ip_address"
    MAC_ADDRESS = "mac_address"
    COOKIE_ID = "cookie_id"
    DEVICE_ID = "device_id"
    
    # Biometric
    FINGERPRINT = "fingerprint"
    FACIAL_RECOGNITION = "facial_recognition"
    
    # Other
    DATE_OF_BIRTH = "date_of_birth"
    GENDER = "gender"
    NATIONALITY = "nationality"


class PrivacyRegulation(str, Enum):
    """Privacy regulations supported."""
    
    GDPR = "gdpr"  # EU General Data Protection Regulation
    PDPA = "pdpa"  # Singapore Personal Data Protection Act
    CCPA = "ccpa"  # California Consumer Privacy Act
    AUSTRALIA_PRIVACY = "australia_privacy"  # Australia Privacy Act
    HIPAA = "hipaa"  # US Health Insurance Portability and Accountability Act


@dataclass
class PIIMatch:
    """Matched PII instance."""
    
    category: PIICategory
    value: str
    start_position: int
    end_position: int
    confidence: float
    regulation_tags: list[PrivacyRegulation] = field(default_factory=list)


@dataclass
class PIIDetectionResult:
    """Result of PII detection scan."""
    
    has_pii: bool
    matches: list[PIIMatch] = field(default_factory=list)
    categories_found: set[PIICategory] = field(default_factory=set)
    risk_score: float = 0.0
    recommended_action: str = "allow"
    masked_content: str | None = None


class PIIDetector:
    """Detects and classifies Personally Identifiable Information."""
    
    # Risk weights for different PII categories
    RISK_WEIGHTS: dict[PIICategory, float] = {
        PIICategory.SSN: 1.0,
        PIICategory.PASSPORT: 0.95,
        PIICategory.CREDIT_CARD: 0.9,
        PIICategory.BANK_ACCOUNT: 0.9,
        PIICategory.MEDICAL_RECORD: 0.95,
        PIICategory.HEALTH_INSURANCE: 0.85,
        PIICategory.DRIVERS_LICENSE: 0.8,
        PIICategory.TAX_ID: 0.85,
        PIICategory.EMAIL: 0.4,
        PIICategory.PHONE: 0.5,
        PIICategory.ADDRESS: 0.6,
        PIICategory.NAME: 0.3,
        PIICategory.IP_ADDRESS: 0.5,
        PIICategory.DATE_OF_BIRTH: 0.6,
        PIICategory.GENDER: 0.2,
        PIICategory.NATIONALITY: 0.2,
    }
    
    def __init__(self) -> None:
        self.patterns: dict[PIICategory, list[tuple[str, re.Pattern]]] = {}
        self._initialize_patterns()
    
    def _initialize_patterns(self) -> None:
        """Initialize regex patterns for PII detection."""
        
        # Email
        self.patterns[PIICategory.EMAIL] = [
            ("email_standard", re.compile(
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            )),
        ]
        
        # Phone numbers (international format)
        self.patterns[PIICategory.PHONE] = [
            ("phone_intl", re.compile(
                r'(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{4}'
            )),
            ("phone_us", re.compile(
                r'\b(?:\d{3}[-.\s]?\d{3}[-.\s]?\d{4})\b'
            )),
        ]
        
        # SSN (US)
        self.patterns[PIICategory.SSN] = [
            ("ssn_us", re.compile(r'\b\d{3}-\d{2}-\d{4}\b')),
            ("ssn_us_nodash", re.compile(r'\b\d{9}\b')),
        ]
        
        # Credit Cards
        self.patterns[PIICategory.CREDIT_CARD] = [
            ("visa", re.compile(r'\b4[0-9]{12}(?:[0-9]{3})?\b')),
            ("mastercard", re.compile(r'\b5[1-5][0-9]{14}\b')),
            ("amex", re.compile(r'\b3[47][0-9]{13}\b')),
            ("discover", re.compile(r'\b6(?:011|5[0-9]{2})[0-9]{12}\b')),
        ]
        
        # IP Addresses
        self.patterns[PIICategory.IP_ADDRESS] = [
            ("ipv4", re.compile(r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b')),
            ("ipv6", re.compile(r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b')),
        ]
        
        # Date of Birth
        self.patterns[PIICategory.DATE_OF_BIRTH] = [
            ("dob_iso", re.compile(r'\b(?:19|20)\d{2}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])\b')),
            ("dob_us", re.compile(r'\b(?:0[1-9]|1[0-2])/(?:0[1-9]|[12]\d|3[01])/(?:19|20)\d{2}\b')),
        ]
        
        # Passport (generic pattern - varies by country)
        self.patterns[PIICategory.PASSPORT] = [
            ("passport_generic", re.compile(r'\b[A-Z]{1,2}\d{6,9}\b')),
        ]
        
        # Bank Account (generic)
        self.patterns[PIICategory.BANK_ACCOUNT] = [
            ("bank_account_us", re.compile(r'\b\d{8,17}\b')),
        ]
        
        # IBAN (International Bank Account Number)
        self.patterns[PIICategory.IBAN] = [
            ("iban", re.compile(r'\b[A-Z]{2}\d{2}[A-Z0-9]{4,30}\b')),
        ]
    
    def detect(self, text: str, min_confidence: float = 0.5) -> PIIDetectionResult:
        """Detect PII in the given text."""
        matches: list[PIIMatch] = []
        categories_found: set[PIICategory] = set()
        
        for category, pattern_list in self.patterns.items():
            for pattern_name, pattern in pattern_list:
                for match in pattern.finditer(text):
                    matched_text = match.group()
                    
                    # Calculate confidence based on pattern specificity
                    confidence = self._calculate_confidence(category, pattern_name, matched_text)
                    
                    if confidence >= min_confidence:
                        pii_match = PIIMatch(
                            category=category,
                            value=matched_text,
                            start_position=match.start(),
                            end_position=match.end(),
                            confidence=confidence,
                            regulation_tags=self._get_regulation_tags(category),
                        )
                        matches.append(pii_match)
                        categories_found.add(category)
        
        # Remove overlapping matches (keep highest confidence)
        matches = self._remove_overlaps(matches)
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(matches)
        
        # Determine recommended action
        recommended_action = self._recommend_action(risk_score, categories_found)
        
        # Generate masked content
        masked_content = self._mask_pii(text, matches) if matches else None
        
        return PIIDetectionResult(
            has_pii=len(matches) > 0,
            matches=matches,
            categories_found=categories_found,
            risk_score=risk_score,
            recommended_action=recommended_action,
            masked_content=masked_content,
        )
    
    def _calculate_confidence(
        self, 
        category: PIICategory, 
        pattern_name: str, 
        matched_text: str
    ) -> float:
        """Calculate confidence score for a PII match."""
        base_confidence = 0.7
        
        # Adjust based on category
        if category in [PIICategory.SSN, PIICategory.CREDIT_CARD]:
            base_confidence = 0.9
        elif category in [PIICategory.EMAIL, PIICategory.PHONE]:
            base_confidence = 0.85
        
        # Adjust based on pattern specificity
        if "standard" in pattern_name or "us" in pattern_name:
            base_confidence += 0.05
        
        # Adjust based on match length (longer matches often more reliable)
        length_factor = min(len(matched_text) / 20.0, 0.1)
        
        return min(base_confidence + length_factor, 1.0)
    
    def _get_regulation_tags(self, category: PIICategory) -> list[PrivacyRegulation]:
        """Get applicable privacy regulations for a PII category."""
        # Most PII is covered by all major regulations
        all_regs = list(PrivacyRegulation)
        
        if category in [PIICategory.MEDICAL_RECORD, PIICategory.HEALTH_INSURANCE]:
            return [PrivacyRegulation.HIPAA, PrivacyRegulation.GDPR]
        
        return all_regs
    
    def _remove_overlaps(self, matches: list[PIIMatch]) -> list[PIIMatch]:
        """Remove overlapping matches, keeping highest confidence."""
        if not matches:
            return []
        
        # Sort by start position
        sorted_matches = sorted(matches, key=lambda m: m.start_position)
        
        result = [sorted_matches[0]]
        for match in sorted_matches[1:]:
            last_match = result[-1]
            
            # Check for overlap
            if match.start_position < last_match.end_position:
                # Overlap detected - keep higher confidence
                if match.confidence > last_match.confidence:
                    result[-1] = match
            else:
                result.append(match)
        
        return result
    
    def _calculate_risk_score(self, matches: list[PIIMatch]) -> float:
        """Calculate overall risk score based on detected PII."""
        if not matches:
            return 0.0
        
        total_risk = 0.0
        for match in matches:
            weight = self.RISK_WEIGHTS.get(match.category, 0.5)
            total_risk += weight * match.confidence
        
        # Normalize to 0-1 range
        return min(total_risk / len(matches), 1.0)
    
    def _recommend_action(self, risk_score: float, categories: set[PIICategory]) -> str:
        """Recommend action based on risk assessment."""
        high_risk_categories = {
            PIICategory.SSN, PIICategory.CREDIT_CARD, 
            PIICategory.MEDICAL_RECORD, PIICategory.PASSPORT
        }
        
        if any(cat in high_risk_categories for cat in categories):
            return "block_or_redact"
        elif risk_score > 0.7:
            return "redact"
        elif risk_score > 0.4:
            return "alert"
        else:
            return "allow"
    
    def _mask_pii(self, text: str, matches: list[PIIMatch]) -> str:
        """Mask PII in text with asterisks."""
        # Sort by position (reverse to maintain indices)
        sorted_matches = sorted(matches, key=lambda m: m.start_position, reverse=True)
        
        result = text
        for match in sorted_matches:
            masked_value = "*" * len(match.value)
            result = (
                result[:match.start_position] + 
                masked_value + 
                result[match.end_position:]
            )
        
        return result
    
    def get_statistics(self, text: str) -> dict[str, Any]:
        """Get PII statistics for the given text."""
        result = self.detect(text)
        
        category_counts: dict[str, int] = {}
        for match in result.matches:
            cat_name = match.category.value
            category_counts[cat_name] = category_counts.get(cat_name, 0) + 1
        
        return {
            "total_pii_instances": len(result.matches),
            "unique_categories": len(result.categories_found),
            "category_breakdown": category_counts,
            "risk_score": result.risk_score,
            "has_high_risk_pii": result.risk_score > 0.7,
        }


# Global PII detector instance
_pii_detector: PIIDetector | None = None


def get_pii_detector() -> PIIDetector:
    """Get or create the global PII detector instance."""
    global _pii_detector
    if _pii_detector is None:
        _pii_detector = PIIDetector()
    return _pii_detector
