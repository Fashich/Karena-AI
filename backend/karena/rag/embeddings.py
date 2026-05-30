"""Embedding model management with versioning support."""

from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer

from karena.config import get_settings


class EmbeddingService:
    def __init__(self) -> None:
        settings = get_settings()
        self.model_name = settings.embedding_model
        self.dimension = settings.embedding_dim
        self._model = SentenceTransformer(self.model_name)

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        vectors = self._model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return np.asarray(vectors, dtype=np.float32)

    def embed_query(self, query: str) -> list[float]:
        return self.embed_texts([query])[0].tolist()


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
