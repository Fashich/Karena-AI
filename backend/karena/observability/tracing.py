"""Distributed tracing for Karena AI with OpenTelemetry integration.

Provides end-to-end request tracing across RAG pipeline components,
enabling performance profiling, bottleneck detection, and root cause analysis.
"""

import time
from contextvars import ContextVar
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4


class SpanStatus(str, Enum):
    """Span execution status."""

    OK = "ok"
    ERROR = "error"
    UNSET = "unset"


@dataclass
class Span:
    """Represents a single span in a trace."""

    trace_id: str
    span_id: str
    parent_span_id: str | None
    name: str
    start_time: float
    end_time: float | None = None
    status: SpanStatus = SpanStatus.UNSET
    attributes: dict[str, Any] = field(default_factory=dict)
    events: list[dict] = field(default_factory=list)
    error_message: str | None = None


@dataclass
class Trace:
    """Complete trace containing multiple spans."""

    trace_id: str
    root_span: Span
    child_spans: list[Span] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


# Context variable for current span
_current_span: ContextVar[Span | None] = ContextVar("current_span", default=None)

# In-memory trace store (production: export to Jaeger/Zipkin)
_traces: dict[str, Trace] = {}


class Tracer:
    """Distributed tracer for RAG pipeline instrumentation."""

    def __init__(self, service_name: str = "karena-ai") -> None:
        self.service_name = service_name
        self._traces = _traces

    def start_trace(
        self,
        name: str,
        attributes: dict[str, Any] | None = None,
    ) -> Span:
        """Start a new trace with root span."""
        trace_id = str(uuid4())
        span_id = str(uuid4())[:16]

        span = Span(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=None,
            name=name,
            start_time=time.time(),
            attributes=attributes or {},
        )

        trace = Trace(
            trace_id=trace_id,
            root_span=span,
        )

        self._traces[trace_id] = trace
        _current_span.set(span)

        return span

    def start_span(
        self,
        name: str,
        attributes: dict[str, Any] | None = None,
    ) -> Span:
        """Start a child span under current span."""
        parent = _current_span.get()
        if not parent:
            return self.start_trace(name, attributes)

        span_id = str(uuid4())[:16]
        span = Span(
            trace_id=parent.trace_id,
            span_id=span_id,
            parent_span_id=parent.span_id,
            name=name,
            start_time=time.time(),
            attributes=attributes or {},
        )

        trace = self._traces.get(parent.trace_id)
        if trace:
            trace.child_spans.append(span)

        _current_span.set(span)
        return span

    def end_span(self, span: Span, status: SpanStatus = SpanStatus.OK) -> None:
        """End a span."""
        span.end_time = time.time()
        span.status = status
        _current_span.set(None)

    def record_error(self, span: Span, error: Exception) -> None:
        """Record an error in a span."""
        span.status = SpanStatus.ERROR
        span.error_message = str(error)
        span.events.append(
            {
                "name": "exception",
                "timestamp": time.time(),
                "attributes": {
                    "exception.type": type(error).__name__,
                    "exception.message": str(error),
                },
            }
        )

    def add_event(
        self,
        span: Span,
        name: str,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        """Add an event to a span."""
        span.events.append(
            {
                "name": name,
                "timestamp": time.time(),
                "attributes": attributes or {},
            }
        )

    def get_trace(self, trace_id: str) -> Trace | None:
        """Retrieve a trace by ID."""
        return self._traces.get(trace_id)

    def get_all_traces(self, limit: int = 100) -> list[Trace]:
        """Get all traces."""
        traces = list(self._traces.values())
        traces.sort(key=lambda t: t.start_time, reverse=True)
        return traces[:limit]

    def export_trace(self, trace_id: str) -> dict[str, Any]:
        """Export trace in standard format."""
        trace = self._traces.get(trace_id)
        if not trace:
            return {}

        def span_to_dict(span: Span) -> dict:
            return {
                "trace_id": span.trace_id,
                "span_id": span.span_id,
                "parent_span_id": span.parent_span_id,
                "name": span.name,
                "start_time": span.start_time,
                "end_time": span.end_time,
                "status": span.status.value,
                "attributes": span.attributes,
                "events": span.events,
                "error_message": span.error_message,
            }

        return {
            "trace_id": trace.trace_id,
            "service_name": self.service_name,
            "start_time": trace.start_time,
            "end_time": trace.end_time,
            "duration_ms": ((trace.end_time or time.time()) - trace.start_time) * 1000,
            "root_span": span_to_dict(trace.root_span),
            "child_spans": [span_to_dict(s) for s in trace.child_spans],
            "metadata": trace.metadata,
        }

    def calculate_latency_breakdown(self, trace_id: str) -> dict[str, float]:
        """Calculate latency breakdown by span."""
        trace = self._traces.get(trace_id)
        if not trace:
            return {}

        breakdown = {}

        # Root span total
        if trace.root_span.end_time:
            breakdown["total"] = (trace.root_span.end_time - trace.root_span.start_time) * 1000

        # Child spans
        for span in trace.child_spans:
            if span.end_time:
                duration = (span.end_time - span.start_time) * 1000
                breakdown[span.name] = duration

        return breakdown


# Global tracer instance
_tracer: Tracer | None = None


def get_tracer() -> Tracer:
    """Get or create tracer instance."""
    global _tracer
    if _tracer is None:
        _tracer = Tracer()
    return _tracer


# Context manager for automatic span management
class trace_context:
    """Context manager for tracing."""

    def __init__(self, name: str, attributes: dict[str, Any] | None = None):
        self.name = name
        self.attributes = attributes
        self.tracer = get_tracer()
        self.span: Span | None = None

    def __enter__(self) -> Span:
        self.span = self.tracer.start_span(self.name, self.attributes)
        return self.span

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span:
            if exc_type:
                self.tracer.record_error(self.span, exc_val)
            else:
                self.tracer.end_span(self.span)
        return False


# RAG Pipeline specific tracing helpers
def trace_rag_query(query: str, tenant_id: str) -> trace_context:
    """Create trace context for RAG query."""
    return trace_context(
        "rag_query",
        {
            "query_length": len(query),
            "tenant_id": tenant_id,
            "query_preview": query[:100],
        },
    )


def trace_retrieval(collection: str, k: int) -> trace_context:
    """Create trace context for retrieval operation."""
    return trace_context(
        "vector_retrieval",
        {"collection": collection, "top_k": k},
    )


def trace_reranking(model: str, input_count: int) -> trace_context:
    """Create trace context for re-ranking operation."""
    return trace_context(
        "semantic_reranking",
        {"model": model, "input_documents": input_count},
    )


def trace_llm_generation(model: str, prompt_length: int) -> trace_context:
    """Create trace context for LLM generation."""
    return trace_context(
        "llm_generation",
        {"model": model, "prompt_tokens": prompt_length},
    )
