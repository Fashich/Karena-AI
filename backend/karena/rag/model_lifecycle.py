"""Embedding model lifecycle management with versioning and retraining hooks.

Handles:
- Model registration and versioning
- Drift detection and retraining triggers
- Model evaluation metrics
- Canary deployments of new models
- Rollback capabilities
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable
from uuid import uuid4

from karena.config import get_settings


class ModelStatus(str, Enum):
    """Model deployment status."""

    CANDIDATE = "candidate"  # Under evaluation
    STABLE = "stable"  # Production baseline
    CANARY = "canary"  # Canary deployment (partial traffic)
    DEPRECATED = "deprecated"  # Scheduled for retirement
    RETIRED = "retired"  # No longer available


class ModelEvaluationMetric(str, Enum):
    """Standard evaluation metrics for embeddings."""

    SEMANTIC_SIMILARITY = "semantic_similarity"
    RETRIEVAL_RECALL = "retrieval_recall"
    RETRIEVAL_PRECISION = "retrieval_precision"
    LATENCY_P95 = "latency_p95"
    LATENCY_P99 = "latency_p99"
    COST_PER_1K_TOKENS = "cost_per_1k_tokens"
    DRIFT_SCORE = "drift_score"


@dataclass
class ModelEvaluation:
    """Evaluation results for a model."""

    evaluation_id: str
    model_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metrics: dict[ModelEvaluationMetric, float] = field(default_factory=dict)
    sample_count: int = 0
    dataset_id: str | None = None
    notes: str = ""
    passed_quality_gate: bool = False

    def get_metric(self, metric: ModelEvaluationMetric) -> float | None:
        return self.metrics.get(metric)


@dataclass
class EmbeddingModelVersion:
    """Represents a versioned embedding model."""

    model_id: str
    version: str
    model_name: str  # HuggingFace model ID
    source: str = "sentence-transformers"
    dimension: int = 384
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: ModelStatus = ModelStatus.CANDIDATE
    promoted_at: datetime | None = None
    deprecated_at: datetime | None = None
    retired_at: datetime | None = None
    evaluations: list[ModelEvaluation] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    canary_traffic_percentage: float = 0.0  # 0-100% traffic for canary models

    def is_production_ready(self) -> bool:
        """Check if model is safe for production use."""
        return self.status in (ModelStatus.STABLE, ModelStatus.CANARY)

    def add_evaluation(self, evaluation: ModelEvaluation) -> None:
        """Add an evaluation result."""
        self.evaluations.append(evaluation)

    def latest_evaluation(self) -> ModelEvaluation | None:
        """Get the most recent evaluation."""
        if not self.evaluations:
            return None
        return sorted(self.evaluations, key=lambda e: e.timestamp, reverse=True)[0]


class EmbeddingModelRegistry:
    """Manages embedding model versions, deployments, and retraining."""

    def __init__(self) -> None:
        self._models: dict[str, EmbeddingModelVersion] = {}
        self._current_model_id: str | None = None
        self._retraining_hooks: list[Callable[[str], None]] = []
        self._load_default_models()

    def _load_default_models(self) -> None:
        """Initialize with default embedding model."""
        settings = get_settings()
        default_model_name = settings.embedding_model
        model_id = str(uuid4())

        model = EmbeddingModelVersion(
            model_id=model_id,
            version="1.0.0",
            model_name=default_model_name,
            dimension=settings.embedding_dim,
            status=ModelStatus.STABLE,
            promoted_at=datetime.now(timezone.utc),
        )

        self._models[model_id] = model
        self._current_model_id = model_id

    def register_model(
        self,
        model_name: str,
        version: str,
        *,
        dimension: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> EmbeddingModelVersion:
        """Register a new model version for evaluation."""
        settings = get_settings()
        model_id = str(uuid4())
        dim = dimension or settings.embedding_dim

        model = EmbeddingModelVersion(
            model_id=model_id,
            version=version,
            model_name=model_name,
            dimension=dim,
            status=ModelStatus.CANDIDATE,
            metadata=metadata or {},
        )

        self._models[model_id] = model
        return model

    def promote_to_canary(
        self,
        model_id: str,
        *,
        traffic_percentage: float = 10.0,
    ) -> bool:
        """Promote a model to canary (gradual rollout)."""
        model = self._models.get(model_id)
        if not model or model.status != ModelStatus.CANDIDATE:
            return False

        model.status = ModelStatus.CANARY
        model.canary_traffic_percentage = min(100.0, max(0.0, traffic_percentage))
        return True

    def promote_to_stable(self, model_id: str) -> bool:
        """Promote a model to stable (full rollout)."""
        model = self._models.get(model_id)
        if not model or model.status not in (ModelStatus.CANARY, ModelStatus.CANDIDATE):
            return False

        # Deprecate current stable model if exists
        if self._current_model_id and self._current_model_id != model_id:
            old_model = self._models.get(self._current_model_id)
            if old_model:
                old_model.status = ModelStatus.DEPRECATED
                old_model.deprecated_at = datetime.now(timezone.utc)

        model.status = ModelStatus.STABLE
        model.promoted_at = datetime.now(timezone.utc)
        model.canary_traffic_percentage = 0.0
        self._current_model_id = model_id
        return True

    def deprecate_model(self, model_id: str) -> bool:
        """Deprecate a model (schedule for retirement)."""
        model = self._models.get(model_id)
        if not model or model.status in (ModelStatus.DEPRECATED, ModelStatus.RETIRED):
            return False

        model.status = ModelStatus.DEPRECATED
        model.deprecated_at = datetime.now(timezone.utc)
        return True

    def retire_model(self, model_id: str) -> bool:
        """Retire a model (remove from service)."""
        model = self._models.get(model_id)
        if not model:
            return False

        model.status = ModelStatus.RETIRED
        model.retired_at = datetime.now(timezone.utc)
        return True

    def get_current_model(self) -> EmbeddingModelVersion | None:
        """Get the currently active (stable) model."""
        if self._current_model_id:
            return self._models.get(self._current_model_id)
        return None

    def get_canary_model(self) -> EmbeddingModelVersion | None:
        """Get the current canary model if any."""
        for model in self._models.values():
            if model.status == ModelStatus.CANARY:
                return model
        return None

    def get_model(self, model_id: str) -> EmbeddingModelVersion | None:
        """Get a specific model by ID."""
        return self._models.get(model_id)

    def list_models(
        self,
        status: ModelStatus | None = None,
    ) -> list[EmbeddingModelVersion]:
        """List models, optionally filtered by status."""
        models = list(self._models.values())
        if status:
            models = [m for m in models if m.status == status]
        return sorted(models, key=lambda m: m.created_at, reverse=True)

    def register_retraining_hook(self, hook: Callable[[str], None]) -> None:
        """Register a callback for model retraining (called with model_id)."""
        self._retraining_hooks.append(hook)

    def trigger_retraining(self, model_id: str) -> None:
        """Trigger retraining for a model (invokes all registered hooks)."""
        for hook in self._retraining_hooks:
            try:
                hook(model_id)
            except Exception:
                pass  # Log and continue

    def add_evaluation(
        self,
        model_id: str,
        metrics: dict[ModelEvaluationMetric, float],
        *,
        sample_count: int = 0,
        dataset_id: str | None = None,
        notes: str = "",
    ) -> ModelEvaluation | None:
        """Add an evaluation result to a model."""
        model = self._models.get(model_id)
        if not model:
            return None

        eval_id = str(uuid4())
        evaluation = ModelEvaluation(
            evaluation_id=eval_id,
            model_id=model_id,
            metrics=metrics,
            sample_count=sample_count,
            dataset_id=dataset_id,
            notes=notes,
        )

        # Check quality gate (example: retrieval precision > 0.75)
        precision = metrics.get(ModelEvaluationMetric.RETRIEVAL_PRECISION, 0.0)
        evaluation.passed_quality_gate = precision > 0.75

        model.add_evaluation(evaluation)
        return evaluation

    def should_trigger_retraining(
        self,
        drift_threshold: float = 0.15,
    ) -> bool:
        """Check if current model should trigger retraining based on drift."""
        model = self.get_current_model()
        if not model:
            return False

        latest_eval = model.latest_evaluation()
        if not latest_eval:
            return False

        drift_score = latest_eval.get_metric(ModelEvaluationMetric.DRIFT_SCORE)
        if drift_score is None:
            return False

        return drift_score >= drift_threshold


_model_registry: EmbeddingModelRegistry | None = None


def get_embedding_model_registry() -> EmbeddingModelRegistry:
    """Get or create the global embedding model registry."""
    global _model_registry
    if _model_registry is None:
        _model_registry = EmbeddingModelRegistry()
    return _model_registry
