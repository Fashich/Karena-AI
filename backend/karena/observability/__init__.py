"""Karena AI Observability Module.

Provides metrics, tracing, and demo scripts for comprehensive
system monitoring and client demonstrations.
"""

from karena.observability.metrics import QUERY_COUNTER, QUERY_LATENCY, setup_metrics
from karena.observability.tracing import (
    Tracer,
    get_tracer,
    trace_context,
    trace_rag_query,
    trace_retrieval,
    trace_reranking,
    trace_llm_generation,
    SpanStatus,
)
from karena.observability.demo_scripts import (
    DemoOrchestrator,
    DemoScenario,
    DemoSession,
    get_demo_orchestrator,
    list_available_scenarios,
    generate_executive_slide_deck,
)

__all__ = [
    "QUERY_COUNTER",
    "QUERY_LATENCY",
    "setup_metrics",
    "Tracer",
    "get_tracer",
    "trace_context",
    "trace_rag_query",
    "trace_retrieval",
    "trace_reranking",
    "trace_llm_generation",
    "SpanStatus",
    "DemoOrchestrator",
    "DemoScenario",
    "DemoSession",
    "get_demo_orchestrator",
    "list_available_scenarios",
    "generate_executive_slide_deck",
]
