"""Prometheus metrics and request instrumentation."""

from prometheus_client import Counter, Gauge, Histogram, generate_latest
from starlette.responses import Response

QUERY_COUNTER = Counter(
    "karena_queries_total",
    "Total RAG queries processed",
    ["tenant_id", "status"],
)
FEEDBACK_COUNTER = Counter(
    "karena_feedback_total",
    "Total feedback events submitted",
    ["tenant_id", "rating"],
)
DLP_COUNTER = Counter(
    "karena_dlp_events_total",
    "Total DLP/PII events detected",
    ["tenant_id", "surface", "action"],
)
QUERY_LATENCY = Histogram(
    "karena_query_latency_seconds",
    "RAG query latency",
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)
RETRIEVAL_COUNT = Histogram(
    "karena_retrieved_documents",
    "Documents retrieved before reranking",
    buckets=[0, 1, 3, 5, 10, 25, 50, 100],
)
LAST_CONFIDENCE = Gauge(
    "karena_last_response_confidence",
    "Confidence score from the latest RAG response",
    ["tenant_id"],
)

# Authentication & Authorization Metrics
AUTH_COUNTER = Counter(
    "karena_auth_events_total",
    "Authentication events",
    ["tenant_id", "event_type"],
)
RATE_LIMIT_COUNTER = Counter(
    "karena_rate_limit_exceeded_total",
    "Rate limit violations",
    ["tenant_id", "user_id"],
)
SESSION_GAUGE = Gauge(
    "karena_active_sessions",
    "Number of active sessions",
    ["tenant_id"],
)

# Embedding Model Lifecycle Metrics
MODEL_EVALUATION_GAUGE = Gauge(
    "karena_model_evaluation_metric",
    "Model evaluation metrics",
    ["model_id", "version", "metric_name"],
)
MODEL_DRIFT_GAUGE = Gauge(
    "karena_model_drift_score",
    "Corpus drift score for deployed model",
    ["model_id", "version"],
)
MODEL_STATUS_GAUGE = Gauge(
    "karena_model_status",
    "Model deployment status (1=candidate, 2=canary, 3=stable, 4=deprecated, 5=retired)",
    ["model_id", "version"],
)
CACHE_HIT_RATIO_GAUGE = Gauge(
    "karena_cache_hit_ratio",
    "Cache hit rate (0.0-1.0)",
    ["tenant_id"],
)


    QUERY_COUNTER.labels(tenant_id=tenant_id, status=status).inc()
    QUERY_LATENCY.observe(latency_ms / 1000)
    RETRIEVAL_COUNT.observe(retrieved_count)


def record_feedback(rating: int, tenant_id: str = "default") -> None:
    label = "positive" if rating > 0 else "negative" if rating < 0 else "neutral"
    FEEDBACK_COUNTER.labels(tenant_id=tenant_id, rating=label).inc()


def record_dlp_event(tenant_id: str, surface: str, action: str) -> None:
    DLP_COUNTER.labels(tenant_id=tenant_id, surface=surface, action=action).inc()


def record_auth_event(tenant_id: str, event_type: str) -> None:
    """Record authentication/authorization event."""
    AUTH_COUNTER.labels(tenant_id=tenant_id, event_type=event_type).inc()


def record_rate_limit(tenant_id: str, user_id: str) -> None:
    """Record rate limit violation."""
    RATE_LIMIT_COUNTER.labels(tenant_id=tenant_id, user_id=user_id).inc()


def set_active_sessions(tenant_id: str, count: int) -> None:
    """Update active session count."""
    SESSION_GAUGE.labels(tenant_id=tenant_id).set(count)


def record_model_evaluation(model_id: str, version: str, metric_name: str, value: float) -> None:
    """Record embedding model evaluation metric."""
    MODEL_EVALUATION_GAUGE.labels(
        model_id=model_id,
        version=version,
        metric_name=metric_name,
    ).set(value)


def set_model_drift_score(model_id: str, version: str, score: float) -> None:
    """Update corpus drift score for a model."""
    MODEL_DRIFT_GAUGE.labels(model_id=model_id, version=version).set(score)


def set_model_status(model_id: str, version: str, status_code: int) -> None:
    """Update model deployment status (1-5)."""
    MODEL_STATUS_GAUGE.labels(model_id=model_id, version=version).set(status_code)


def set_cache_hit_ratio(tenant_id: str, ratio: float) -> None:
    """Update cache hit ratio (0.0-1.0)."""
    CACHE_HIT_RATIO_GAUGE.labels(tenant_id=tenant_id).set(ratio)


def setup_metrics(app) -> None:
    @app.get("/metrics")
    async def metrics():
        return Response(generate_latest(), media_type="text/plain")
