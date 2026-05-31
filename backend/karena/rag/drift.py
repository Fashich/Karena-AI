from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from karena.rag.embeddings import get_embedding_service


@dataclass
class DriftReport:
    tenant_id: str
    baseline_center: list[float]
    current_center: list[float]
    drift_score: float
    sample_size: int
    threshold: float
    status: str
    details: dict[str, Any] = field(default_factory=dict)


class CorpusDriftDetector:
    """Lightweight corpus drift detector using embedding centroid drift."""

    def __init__(self, threshold: float = 0.15) -> None:
        self.threshold = threshold
        self._tenant_baselines: dict[str, list[float]] = {}

    def update_baseline(self, tenant_id: str, texts: list[str]) -> None:
        if not texts:
            return
        import numpy as np

        embeddings = np.asarray(get_embedding_service().embed_texts(texts), dtype=np.float32)
        self._tenant_baselines[tenant_id] = embeddings.mean(axis=0).tolist()

    def detect_drift(self, tenant_id: str, texts: list[str]) -> DriftReport | None:
        if not texts:
            return None

        import numpy as np

        embeddings = np.asarray(get_embedding_service().embed_texts(texts), dtype=np.float32)
        current_center = embeddings.mean(axis=0)
        baseline = self._tenant_baselines.get(tenant_id)
        if baseline is None:
            self.update_baseline(tenant_id, texts)
            baseline = self._tenant_baselines[tenant_id]

        baseline_center = np.asarray(baseline)
        drift_score = float(1.0 - np.dot(current_center, baseline_center) / (np.linalg.norm(current_center) * np.linalg.norm(baseline_center) + 1e-12))
        status = "drift_detected" if drift_score >= self.threshold else "stable"

        return DriftReport(
            tenant_id=tenant_id,
            baseline_center=baseline_center.tolist(),
            current_center=current_center.tolist(),
            drift_score=drift_score,
            sample_size=len(texts),
            threshold=self.threshold,
            status=status,
            details={"baseline_exists": tenant_id in self._tenant_baselines},
        )


_drift_detector: CorpusDriftDetector | None = None


def get_drift_detector() -> CorpusDriftDetector:
    global _drift_detector
    if _drift_detector is None:
        _drift_detector = CorpusDriftDetector()
    return _drift_detector
