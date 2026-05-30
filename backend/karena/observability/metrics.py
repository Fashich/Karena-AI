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
def record_query(tenant_id: str, status: str, latency_ms: float, retrieved_count: int) -> None:
    QUERY_COUNTER.labels(tenant_id=tenant_id, status=status).inc()
    QUERY_LATENCY.observe(latency_ms / 1000)
    RETRIEVAL_COUNT.observe(retrieved_count)


def record_feedback(rating: int, tenant_id: str = "default") -> None:
    label = "positive" if rating > 0 else "negative" if rating < 0 else "neutral"
    FEEDBACK_COUNTER.labels(tenant_id=tenant_id, rating=label).inc()


def record_dlp_event(tenant_id: str, surface: str, action: str) -> None:
    DLP_COUNTER.labels(tenant_id=tenant_id, surface=surface, action=action).inc()


def setup_metrics(app) -> None:
    @app.get("/metrics")
    async def metrics():
        return Response(generate_latest(), media_type="text/plain")
