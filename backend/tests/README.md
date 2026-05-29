# Karena AI Test Coverage Report

## Summary
- **Total Tests**: 50+ test cases across all modules
- **Coverage Target**: 80% minimum
- **Test Categories**: Unit, Integration, Security, API

## Test Modules

### 1. RAG Pipeline Tests (`test_rag.py`)
Tests for retrieval-augmented generation components:
- RAGPipeline initialization and query execution
- HybridRetriever (dense + BM25 fusion)
- VectorStore operations (upsert, search)
- EmbeddingModel encoding
- SemanticReranker ranking

### 2. Security Tests (`test_security.py`)
Tests for security and compliance features:
- DLPEngine pattern detection (credit cards, SSN, API keys)
- PIIDetector email/phone/name detection and masking
- AuditLogger action logging and compliance reporting

### 3. API Tests (`test_api.py`)
Tests for REST API endpoints:
- APIGateway health checks and routing
- ChatEndpoint query processing and rate limiting
- DocumentEndpoint upload/list/delete operations
- Authentication JWT validation and API key auth
- AdminEndpoint role-based access control
- FeedbackEndpoint rating submission

## Running Tests

```bash
# Run all tests
pytest backend/tests/ -v

# Run with coverage
pytest backend/tests/ --cov=karena --cov-report=html

# Run specific test category
pytest backend/tests/test_rag.py -v
pytest backend/tests/test_security.py -v
pytest backend/tests/test_api.py -v

# Run with markers
pytest -m "unit"
pytest -m "integration"
pytest -m "security"
```

## CI/CD Integration
Tests are automatically run in the CI/CD pipeline on every PR:
- Unit tests must pass before merge
- Coverage threshold enforced at 80%
- Security tests run on every commit
