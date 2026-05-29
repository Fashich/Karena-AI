"""
Karena AI RAG Pipeline Tests
Comprehensive test suite for RAG pipeline components
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np


class TestRAGPipeline:
    """Test cases for RAG pipeline orchestration"""

    def test_pipeline_initialization(self):
        """Test that RAG pipeline initializes correctly"""
        from karena.rag.pipeline import RAGPipeline

        # Mock dependencies
        mock_retriever = Mock()
        mock_reranker = Mock()
        mock_llm = Mock()

        pipeline = RAGPipeline(retriever=mock_retriever, reranker=mock_reranker, llm=mock_llm)

        assert pipeline is not None
        assert pipeline.retriever == mock_retriever
        assert pipeline.reranker == mock_reranker
        assert pipeline.llm == mock_llm

    def test_pipeline_query_execution(self):
        """Test pipeline executes query through all stages"""
        from karena.rag.pipeline import RAGPipeline

        # Mock retriever response
        mock_documents = [
            {"content": "Document 1", "score": 0.9},
            {"content": "Document 2", "score": 0.8},
        ]

        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = mock_documents

        # Mock reranker response
        mock_reranker = Mock()
        mock_reranker.rerank.return_value = mock_documents[:1]

        # Mock LLM response
        mock_llm = Mock()
        mock_llm.generate.return_value = "Generated answer based on documents"

        pipeline = RAGPipeline(retriever=mock_retriever, reranker=mock_reranker, llm=mock_llm)

        result = pipeline.query("What is Karena AI?")

        assert result is not None
        assert "answer" in result
        mock_retriever.retrieve.assert_called_once()
        mock_reranker.rerank.assert_called_once()
        mock_llm.generate.assert_called_once()

    def test_pipeline_with_cache_hit(self):
        """Test pipeline uses cache when available"""
        from karena.rag.pipeline import RAGPipeline
        from karena.cache.tiers import CacheTier

        mock_cache = Mock(spec=CacheTier)
        mock_cache.get.return_value = {"answer": "Cached response"}

        pipeline = RAGPipeline(retriever=Mock(), reranker=Mock(), llm=Mock(), cache=mock_cache)

        result = pipeline.query("Frequently asked question")

        assert result["answer"] == "Cached response"
        mock_cache.get.assert_called_once()


class TestHybridRetriever:
    """Test cases for hybrid retrieval (dense + BM25)"""

    def test_hybrid_retriever_initialization(self):
        """Test hybrid retriever initializes with both retrievers"""
        from karena.rag.hybrid_retriever import HybridRetriever

        dense_retriever = Mock()
        bm25_retriever = Mock()

        retriever = HybridRetriever(
            dense_retriever=dense_retriever, bm25_retriever=bm25_retriever, alpha=0.7
        )

        assert retriever.dense_retriever == dense_retriever
        assert retriever.bm25_retriever == bm25_retriever
        assert retriever.alpha == 0.7

    def test_hybrid_retrieval_fusion(self):
        """Test hybrid retrieval combines results from both methods"""
        from karena.rag.hybrid_retriever import HybridRetriever

        # Mock dense retrieval results
        dense_results = [
            {"id": "doc1", "content": "Semantic match", "score": 0.9},
            {"id": "doc2", "content": "Another match", "score": 0.7},
        ]

        # Mock BM25 retrieval results
        bm25_results = [
            {"id": "doc3", "content": "Keyword match", "score": 0.8},
            {"id": "doc1", "content": "Semantic match", "score": 0.6},
        ]

        dense_retriever = Mock()
        dense_retriever.retrieve.return_value = dense_results

        bm25_retriever = Mock()
        bm25_retriever.retrieve.return_value = bm25_results

        retriever = HybridRetriever(
            dense_retriever=dense_retriever, bm25_retriever=bm25_retriever, alpha=0.5
        )

        results = retriever.retrieve("query text", top_k=3)

        assert len(results) <= 3
        # doc1 should appear with fused score
        assert any(r["id"] == "doc1" for r in results)


class TestVectorStore:
    """Test cases for vector database operations"""

    def test_vector_store_upsert(self):
        """Test upserting documents to vector store"""
        from karena.rag.vector_store import VectorStore

        mock_client = Mock()
        mock_client.upsert.return_value = {"status": "ok"}

        store = VectorStore(client=mock_client, collection_name="test_collection")

        documents = [{"id": "doc1", "vector": [0.1] * 768, "payload": {"text": "Test"}}]

        result = store.upsert(documents)

        assert result["status"] == "ok"
        mock_client.upsert.assert_called_once()

    def test_vector_store_search(self):
        """Test searching vector store"""
        from karena.rag.vector_store import VectorStore

        mock_client = Mock()
        mock_client.search.return_value = [
            {"id": "doc1", "score": 0.95, "payload": {"text": "Relevant doc"}}
        ]

        store = VectorStore(client=mock_client, collection_name="test_collection")

        query_vector = [0.1] * 768
        results = store.search(query_vector, top_k=5)

        assert len(results) == 1
        assert results[0]["score"] == 0.95
        mock_client.search.assert_called_once()


class TestEmbeddings:
    """Test cases for embedding model management"""

    def test_embedding_model_initialization(self):
        """Test embedding model loads correctly"""
        from karena.rag.embeddings import EmbeddingModel

        with patch("sentence_transformers.SentenceTransformer") as mock_model:
            model = EmbeddingModel(model_name="test-model")

            assert model.model_name == "test-model"
            mock_model.assert_called_once_with("test-model")

    def test_embedding_generation(self):
        """Test generating embeddings for text"""
        from karena.rag.embeddings import EmbeddingModel

        with patch("sentence_transformers.SentenceTransformer") as mock_model_class:
            mock_model = Mock()
            mock_model.encode.return_value = np.array([0.1] * 768)
            mock_model_class.return_value = mock_model

            model = EmbeddingModel(model_name="test-model")
            embedding = model.encode("Sample text")

            assert len(embedding) == 768
            mock_model.encode.assert_called_once_with("Sample text")


class TestReranker:
    """Test cases for semantic re-ranking"""

    def test_reranker_initialization(self):
        """Test reranker initializes correctly"""
        from karena.rag.reranker import SemanticReranker

        with patch("sentence_transformers.CrossEncoder") as mock_encoder:
            reranker = SemanticReranker(model_name="cross-encoder-model")

            assert reranker.model_name == "cross-encoder-model"
            mock_encoder.assert_called_once()

    def test_reranking_documents(self):
        """Test reranking a list of documents"""
        from karena.rag.reranker import SemanticReranker

        with patch("sentence_transformers.CrossEncoder") as mock_encoder_class:
            mock_encoder = Mock()
            mock_encoder.predict.return_value = [0.9, 0.7, 0.8]
            mock_encoder_class.return_value = mock_encoder

            reranker = SemanticReranker(model_name="test-model")

            documents = [{"content": "Doc 1"}, {"content": "Doc 2"}, {"content": "Doc 3"}]

            query = "What is AI?"
            reranked = reranker.rerank(query, documents, top_k=2)

            assert len(reranked) == 2
            # First document should have highest score
            assert reranked[0]["score"] == 0.9


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
