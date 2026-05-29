"""Prometheus metrics and request instrumentation."""

from prometheus_client import Counter, Histogram, generate_latest
from starlette.requests import Request
from starlette.responses import Response

QUERY_COUNTER = Counter(
  "karena_queries_total",
  "Total RAG queries processed",
  ["tenant_id", "status"],
)
QUERY_LATENCY = Histogram(
  "karena_query_latency_seconds",
  "RAG query latency",
  buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)


def setup_metrics(app) -> None:
  @app.get("/metrics")
  async def metrics():
    return Response(generate_latest(), media_type="text/plain")
