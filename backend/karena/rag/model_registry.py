from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from karena.config import get_settings


@dataclass
class EmbeddingModelVersion:
    model_name: str
    version: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    source: str = "sentence-transformers"
    metadata: dict[str, Any] = field(default_factory=dict)
    quality_score: float = 0.0
    status: str = "active"


class ModelRegistry:
    """Simple registry for embedding model versions and evaluation metadata."""

    def __init__(self) -> None:
        self._models: dict[str, EmbeddingModelVersion] = {}
        self._current_model: str | None = None
        self._load_default_models()

    def _load_default_models(self) -> None:
        settings = get_settings()
        default_model_name = settings.embedding_model
        self.register_model(default_model_name, "default", status="active")
        self._current_model = default_model_name

    def register_model(
        self,
        model_name: str,
        version: str,
        *,
        metadata: dict[str, Any] | None = None,
        status: str = "active",
    ) -> EmbeddingModelVersion:
        entry = EmbeddingModelVersion(
            model_name=model_name,
            version=version,
            metadata=metadata or {},
            status=status,
        )
        self._models[model_name] = entry
        if self._current_model is None:
            self._current_model = model_name
        return entry

    def get_current_model(self) -> EmbeddingModelVersion | None:
        if self._current_model:
            return self._models.get(self._current_model)
        return None

    def list_models(self) -> list[EmbeddingModelVersion]:
        return list(self._models.values())

    def set_current_model(self, model_name: str) -> bool:
        if model_name not in self._models:
            return False
        self._current_model = model_name
        return True

    def evaluate_model(self, model_name: str, sample_texts: list[str]) -> dict[str, Any]:
        if model_name not in self._models:
            raise ValueError(f"Unknown model: {model_name}")

        import numpy as np
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer(model_name)
        embeddings = np.asarray(
            model.encode(sample_texts, normalize_embeddings=True, show_progress_bar=False),
            dtype=np.float32,
        )
        mean_norm = float(np.linalg.norm(embeddings, axis=1).mean())
        variance = float(np.var(np.linalg.norm(embeddings, axis=1)))
        return {
            "model_name": model_name,
            "sample_count": len(sample_texts),
            "mean_embedding_norm": mean_norm,
            "embedding_norm_variance": variance,
            "status": self._models[model_name].status,
        }


_registry: ModelRegistry | None = None


def get_model_registry() -> ModelRegistry:
    global _registry
    if _registry is None:
        _registry = ModelRegistry()
    return _registry
