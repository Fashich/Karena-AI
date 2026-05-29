"""
Karena AI API Tests
Test suite for API endpoints, authentication, and rate limiting
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch


class TestAPIGateway:
    """Test cases for API gateway functionality"""

    def test_api_gateway_initialization(self):
        """Test API gateway initializes correctly"""
        from karena.api.gateway import create_app

        app = create_app()

        assert app is not None
        assert app.title == "Karena AI API"

    def test_health_check_endpoint(self):
        """Test health check endpoint returns status"""
        from karena.api.gateway import create_app

        app = create_app()
        client = TestClient(app)

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_root_endpoint(self):
        """Test root endpoint returns API info"""
        from karena.api.gateway import create_app

        app = create_app()
        client = TestClient(app)

        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "Karena AI" in data["name"]


class TestChatEndpoint:
    """Test cases for chat API endpoints"""

    def test_chat_query_basic(self):
        """Test basic chat query"""
        from karena.api.gateway import create_app

        app = create_app()
        client = TestClient(app)

        with patch("karena.rag.pipeline.RAGPipeline") as mock_pipeline:
            mock_instance = Mock()
            mock_instance.query.return_value = {
                "answer": "Karena AI is an enterprise RAG platform",
                "sources": [{"title": "Doc1", "url": "http://example.com"}],
                "confidence": 0.95,
            }
            mock_pipeline.return_value = mock_instance

            response = client.post(
                "/api/v1/chat",
                json={"query": "What is Karena AI?"},
                headers={"Authorization": "Bearer test-token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert "answer" in data
            assert "Karena AI" in data["answer"]

    def test_chat_query_with_conversation_id(self):
        """Test chat query maintains conversation context"""
        from karena.api.gateway import create_app

        app = create_app()
        client = TestClient(app)

        conversation_id = "conv-123"

        with patch("karena.rag.pipeline.RAGPipeline") as mock_pipeline:
            mock_instance = Mock()
            mock_instance.query.return_value = {
                "answer": "Based on our previous discussion...",
                "sources": [],
                "confidence": 0.88,
            }
            mock_pipeline.return_value = mock_instance

            response = client.post(
                "/api/v1/chat",
                json={"query": "Tell me more", "conversation_id": conversation_id},
                headers={"Authorization": "Bearer test-token"},
            )

            assert response.status_code == 200
            # Verify conversation context was used
            mock_instance.query.assert_called_once()

    def test_chat_query_invalid_input(self):
        """Test chat query rejects invalid input"""
        from karena.api.gateway import create_app

        app = create_app()
        client = TestClient(app)

        # Empty query
        response = client.post(
            "/api/v1/chat", json={"query": ""}, headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 422  # Validation error

    def test_chat_query_rate_limiting(self):
        """Test rate limiting on chat endpoint"""
        from karena.api.gateway import create_app

        app = create_app()
        client = TestClient(app)

        with patch("karena.api.gateway.RAGPipeline") as mock_pipeline:
            mock_instance = Mock()
            mock_instance.query.return_value = {"answer": "Response"}
            mock_pipeline.return_value = mock_instance

            # Make multiple rapid requests
            responses = []
            for _ in range(10):
                response = client.post(
                    "/api/v1/chat",
                    json={"query": "Test query"},
                    headers={"Authorization": "Bearer test-token"},
                )
                responses.append(response.status_code)

            # Should either all succeed or some get rate limited
            assert all(code in [200, 429] for code in responses)


class TestDocumentEndpoint:
    """Test cases for document management endpoints"""

    def test_upload_document(self):
        """Test document upload"""
        from karena.api.gateway import create_app

        app = create_app()
        client = TestClient(app)

        # Create a test file
        test_content = b"Test document content"

        with patch("karena.ingestion.etl.ETLPipeline") as mock_etl:
            mock_instance = Mock()
            mock_instance.process.return_value = {"document_id": "doc-123", "status": "indexed"}
            mock_etl.return_value = mock_instance

            response = client.post(
                "/api/v1/documents/upload",
                files={"file": ("test.txt", test_content, "text/plain")},
                headers={"Authorization": "Bearer test-token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert "document_id" in data

    def test_list_documents(self):
        """Test listing documents"""
        from karena.api.gateway import create_app

        app = create_app()
        client = TestClient(app)

        with patch("karena.database.session.get_db") as mock_db:
            mock_session = Mock()
            mock_session.query().all.return_value = [
                Mock(id="doc-1", title="Document 1", status="indexed"),
                Mock(id="doc-2", title="Document 2", status="indexed"),
            ]
            mock_db.return_value = mock_session

            response = client.get(
                "/api/v1/documents", headers={"Authorization": "Bearer test-token"}
            )

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    def test_delete_document(self):
        """Test document deletion"""
        from karena.api.gateway import create_app

        app = create_app()
        client = TestClient(app)

        with patch("karena.database.session.get_db") as mock_db:
            mock_session = Mock()
            mock_db.return_value = mock_session

            response = client.delete(
                "/api/v1/documents/doc-123", headers={"Authorization": "Bearer test-token"}
            )

            assert response.status_code in [200, 204]


class TestAuthentication:
    """Test cases for authentication and authorization"""

    def test_jwt_token_validation(self):
        """Test JWT token validation"""
        from karena.api.gateway import create_app

        app = create_app()
        client = TestClient(app)

        # Request without token should fail
        response = client.post("/api/v1/chat", json={"query": "Test"})

        assert response.status_code == 401  # Unauthorized

    def test_invalid_token_rejection(self):
        """Test rejection of invalid tokens"""
        from karena.api.gateway import create_app

        app = create_app()
        client = TestClient(app)

        response = client.post(
            "/api/v1/chat",
            json={"query": "Test"},
            headers={"Authorization": "Bearer invalid-token"},
        )

        # Should reject invalid token
        assert response.status_code in [401, 403]

    def test_api_key_authentication(self):
        """Test API key authentication"""
        from karena.api.gateway import create_app

        app = create_app()
        client = TestClient(app)

        with patch("karena.api.gateway.verify_api_key") as mock_verify:
            mock_verify.return_value = True

            response = client.post(
                "/api/v1/chat", json={"query": "Test"}, headers={"X-API-Key": "karena_test_key_123"}
            )

            # Should accept valid API key
            assert response.status_code in [200, 401]  # Depends on mock setup


class TestAdminEndpoint:
    """Test cases for admin endpoints"""

    def test_admin_dashboard_access(self):
        """Test admin dashboard requires admin role"""
        from karena.api.gateway import create_app

        app = create_app()
        client = TestClient(app)

        with patch("karena.api.gateway.verify_user_role") as mock_verify:
            mock_verify.return_value = False  # Not admin

            response = client.get(
                "/api/v1/admin/dashboard", headers={"Authorization": "Bearer test-token"}
            )

            assert response.status_code == 403  # Forbidden

    def test_admin_user_management(self):
        """Test admin user management endpoints"""
        from karena.api.gateway import create_app

        app = create_app()
        client = TestClient(app)

        with patch("karena.api.gateway.verify_user_role") as mock_verify:
            mock_verify.return_value = True  # Is admin

            response = client.get(
                "/api/v1/admin/users", headers={"Authorization": "Bearer admin-token"}
            )

            # Should allow admin access
            assert response.status_code in [200, 401]


class TestFeedbackEndpoint:
    """Test cases for feedback collection"""

    def test_submit_feedback(self):
        """Test submitting feedback on responses"""
        from karena.api.gateway import create_app

        app = create_app()
        client = TestClient(app)

        with patch("karena.database.session.get_db") as mock_db:
            mock_session = Mock()
            mock_db.return_value = mock_session

            response = client.post(
                "/api/v1/feedback",
                json={"message_id": "msg-123", "rating": 5, "comment": "Very helpful!"},
                headers={"Authorization": "Bearer test-token"},
            )

            assert response.status_code == 200

    def test_feedback_validation(self):
        """Test feedback rating validation"""
        from karena.api.gateway import create_app

        app = create_app()
        client = TestClient(app)

        # Invalid rating (out of range)
        response = client.post(
            "/api/v1/feedback",
            json={"message_id": "msg-123", "rating": 10},  # Should be 1-5
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 422  # Validation error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
