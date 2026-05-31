"""Embedding model management with versioning support."""

from functools import lru_cache

from karena.config import get_settings
from karena.rag.model_registry import get_model_registry


class EmbeddingService:
    def __init__(self, model_name: str | None = None) -> None:
        from sentence_transformers import SentenceTransformer

        settings = get_settings()
        self.model_name = model_name or (
            get_model_registry().get_current_model().model_name
            if get_model_registry().get_current_model()
            else settings.embedding_model
        )
        self.dimension = settings.embedding_dim
        self._model = SentenceTransformer(self.model_name)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        import numpy as np

        vectors = self._model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return np.asarray(vectors, dtype=np.float32).tolist()

    def embed_query(self, query: str) -> list[float]:
        return self.embed_texts([query])[0]


class EmbeddingModel:
    """Synchronous compatibility wrapper around SentenceTransformer."""

    def __init__(self, model_name: str) -> None:
        import sentence_transformers

        self.model_name = model_name
        self._model = sentence_transformers.SentenceTransformer(model_name)

    def encode(self, text: str):
        return self._model.encode(text)


@lru_cache
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()
