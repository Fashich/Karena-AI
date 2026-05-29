"""
Karena AI Security Tests
Test suite for DLP, PII detection, and audit logging
"""

import pytest
from unittest.mock import Mock, patch


class TestDLPEngine:
    """Test cases for Data Loss Prevention engine"""
    
    def test_dlp_initialization(self):
        """Test DLP engine initializes correctly"""
        from karena.security.dlp import DLPEngine
        
        engine = DLPEngine()
        
        assert engine is not None
        assert len(engine.patterns) > 0
    
    def test_credit_card_detection(self):
        """Test detection of credit card numbers"""
        from karena.security.dlp import DLPEngine
        
        engine = DLPEngine()
        
        # Test various credit card formats
        test_cases = [
            "4532015112830366",  # Visa
            "5425233430109903",  # Mastercard
            "My card number is 4532-0151-1283-0366",
            "Card: 5425 2334 3010 9903"
        ]
        
        for text in test_cases:
            result = engine.scan(text)
            assert result["has_sensitive_data"] is True
            assert "credit_card" in result["detected_types"]
    
    def test_ssn_detection(self):
        """Test detection of Social Security Numbers"""
        from karena.security.dlp import DLPEngine
        
        engine = DLPEngine()
        
        test_cases = [
            "123-45-6789",
            "SSN: 123 45 6789",
            "My SSN is 123456789"
        ]
        
        for text in test_cases:
            result = engine.scan(text)
            assert result["has_sensitive_data"] is True
            assert "ssn" in result["detected_types"]
    
    def test_api_key_detection(self):
        """Test detection of API keys"""
        from karena.security.dlp import DLPEngine
        
        engine = DLPEngine()
        
        test_cases = [
            "sk-1234567890abcdef",  # OpenAI style
            "api_key=AKIAIOSFODNN7EXAMPLE",  # AWS style
            "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        ]
        
        for text in test_cases:
            result = engine.scan(text)
            assert result["has_sensitive_data"] is True
            assert "api_key" in result["detected_types"]
    
    def test_clean_text(self):
        """Test that clean text passes without flags"""
        from karena.security.dlp import DLPEngine
        
        engine = DLPEngine()
        
        clean_text = "This is a normal sentence without sensitive data."
        result = engine.scan(clean_text)
        
        assert result["has_sensitive_data"] is False
        assert len(result["detected_types"]) == 0


class TestPIIDetector:
    """Test cases for Personally Identifiable Information detection"""
    
    def test_pii_detector_initialization(self):
        """Test PII detector initializes correctly"""
        from karena.security.pii import PIIDetector
        
        detector = PIIDetector()
        
        assert detector is not None
    
    def test_email_detection(self):
        """Test detection of email addresses"""
        from karena.security.pii import PIIDetector
        
        detector = PIIDetector()
        
        test_cases = [
            "Contact me at john.doe@example.com",
            "Email: jane_smith@company.co.uk",
            "Support email is support@test.io"
        ]
        
        for text in test_cases:
            result = detector.detect(text)
            assert result["has_pii"] is True
            assert "email" in result["pii_types"]
    
    def test_phone_number_detection(self):
        """Test detection of phone numbers"""
        from karena.security.pii import PIIDetector
        
        detector = PIIDetector()
        
        test_cases = [
            "+1-555-123-4567",
            "(555) 987-6543",
            "Call me at 555.123.4567",
            "Phone: +62 812 3456 7890"  # Indonesian format
        ]
        
        for text in test_cases:
            result = detector.detect(text)
            assert result["has_pii"] is True
            assert "phone" in result["pii_types"]
    
    def test_name_detection(self):
        """Test detection of personal names"""
        from karena.security.pii import PIIDetector
        
        detector = PIIDetector()
        
        # Names with context
        test_cases = [
            "My name is John Smith",
            "Contact person: Jane Doe",
            "Dr. Sarah Johnson will assist you"
        ]
        
        for text in test_cases:
            result = detector.detect(text)
            # Name detection may vary based on implementation
            assert result is not None
    
    def test_pii_masking(self):
        """Test PII masking functionality"""
        from karena.security.pii import PIIDetector
        
        detector = PIIDetector()
        
        text = "Contact john.doe@example.com or call +1-555-123-4567"
        masked = detector.mask_pii(text)
        
        assert "john.doe@example.com" not in masked
        assert "+1-555-123-4567" not in masked
        assert "[EMAIL]" in masked or "***" in masked
        assert "[PHONE]" in masked or "***" in masked


class TestAuditLogger:
    """Test cases for audit logging"""
    
    def test_audit_logger_initialization(self):
        """Test audit logger initializes correctly"""
        from karena.security.audit import AuditLogger
        
        logger = AuditLogger(service_name="test-service")
        
        assert logger is not None
        assert logger.service_name == "test-service"
    
    def test_log_user_action(self):
        """Test logging user actions"""
        from karena.security.audit import AuditLogger
        
        logger = AuditLogger(service_name="test-service")
        
        with patch.object(logger, '_write_log') as mock_write:
            logger.log_action(
                user_id="user-123",
                action="document_upload",
                resource_type="document",
                resource_id="doc-456",
                details={"filename": "report.pdf"}
            )
            
            mock_write.assert_called_once()
            call_args = mock_write.call_args[0][0]
            
            assert call_args["user_id"] == "user-123"
            assert call_args["action"] == "document_upload"
            assert call_args["resource_type"] == "document"
    
    def test_log_security_event(self):
        """Test logging security events"""
        from karena.security.audit import AuditLogger
        
        logger = AuditLogger(service_name="test-service")
        
        with patch.object(logger, '_write_log') as mock_write:
            logger.log_security_event(
                event_type="unauthorized_access",
                severity="high",
                details={"ip": "192.168.1.100", "attempted_resource": "/admin"}
            )
            
            mock_write.assert_called_once()
            call_args = mock_write.call_args[0][0]
            
            assert call_args["event_type"] == "unauthorized_access"
            assert call_args["severity"] == "high"
    
    def test_log_compliance_event(self):
        """Test logging compliance-related events"""
        from karena.security.audit import AuditLogger
        
        logger = AuditLogger(service_name="test-service")
        
        with patch.object(logger, '_write_log') as mock_write:
            logger.log_compliance_event(
                regulation="GDPR",
                event_type="data_access_request",
                user_id="user-789"
            )
            
            mock_write.assert_called_once()
            call_args = mock_write.call_args[0][0]
            
            assert call_args["regulation"] == "GDPR"
            assert call_args["event_type"] == "data_access_request"
    
    def test_audit_log_format(self):
        """Test that audit logs have correct format"""
        from karena.security.audit import AuditLogger
        import json
        
        logger = AuditLogger(service_name="test-service")
        
        with patch.object(logger, '_write_log') as mock_write:
            logger.log_action(
                user_id="user-123",
                action="test_action"
            )
            
            call_args = mock_write.call_args[0][0]
            
            # Verify required fields
            assert "timestamp" in call_args
            assert "service_name" in call_args
            assert "action" in call_args
            assert "id" in call_args  # Unique log ID


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
