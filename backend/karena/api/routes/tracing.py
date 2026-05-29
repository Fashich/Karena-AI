"""API routes for distributed tracing observability."""

from fastapi import APIRouter, Depends, HTTPException

from karena.api.gateway import get_current_user, TokenPayload
from karena.observability.tracing import get_tracer

router = APIRouter()


@router.get("/traces")
async def list_traces(
    limit: int = 100,
    current_user: TokenPayload = Depends(get_current_user),
):
    """List recent traces for observability."""
    tracer = get_tracer()
    traces = tracer.get_all_traces(limit=limit)
    
    return {
        "traces": [
            {
                "trace_id": t.trace_id,
                "start_time": t.start_time,
                "end_time": t.end_time,
                "duration_ms": ((t.end_time or 0) - t.start_time) * 1000,
                "span_count": 1 + len(t.child_spans),
            }
            for t in traces
        ],
        "total": len(traces),
    }


@router.get("/traces/{trace_id}")
async def get_trace(
    trace_id: str,
    current_user: TokenPayload = Depends(get_current_user),
):
    """Get detailed trace information."""
    tracer = get_tracer()
    trace_data = tracer.export_trace(trace_id)
    
    if not trace_data:
        raise HTTPException(status_code=404, detail="Trace not found")
    
    return trace_data


@router.get("/traces/{trace_id}/latency")
async def get_latency_breakdown(
    trace_id: str,
    current_user: TokenPayload = Depends(get_current_user),
):
    """Get latency breakdown for a trace."""
    tracer = get_tracer()
    breakdown = tracer.calculate_latency_breakdown(trace_id)
    
    if not breakdown:
        raise HTTPException(status_code=404, detail="Trace not found")
    
    return {
        "trace_id": trace_id,
        "latency_breakdown_ms": breakdown,
    }
