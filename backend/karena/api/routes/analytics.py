"""
Analytics API routes — Community Decision Intelligence.

Endpoints:
  GET  /analytics/domains           — list all domains + metadata
  GET  /analytics/snapshot          — current-state snapshot across all domains
  POST /analytics/forecast          — time-series forecast for a domain metric
  POST /analytics/anomalies         — anomaly scan for a domain
  GET  /analytics/insights/{domain} — auto-generated insights for a domain
  POST /analytics/query             — domain-routed AI query (multi-agent)
"""

import logging

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from karena.analytics.engine import get_anomaly_detector, get_forecaster, get_insight_generator, get_simulator
from karena.domains.agents import classify_query, get_domain_agent, list_domains

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics", tags=["analytics"])


# ─── Request / Response schemas ──────────────────────────────

class ForecastRequest(BaseModel):
    domain: str = Field(..., description="Community domain id, e.g. 'urban_mobility'")
    metric: str = Field(..., description="Metric name within the domain")
    horizon_days: int = Field(7, ge=1, le=30, description="Forecast horizon in days")
    historical_days: int = Field(14, ge=7, le=90, description="Historical window in days")


class AnomalyRequest(BaseModel):
    domain: str
    metric: str
    historical_days: int = Field(30, ge=7, le=90)


class DomainQueryRequest(BaseModel):
    query: str = Field(..., min_length=3, description="Natural language query")
    domain: str | None = Field(None, description="Force a specific domain (auto-detected if omitted)")
    session_id: str | None = None
    user_id: str = "anonymous"


# ─── Endpoints ───────────────────────────────────────────────

@router.get("/domains")
async def get_domains():
    """List all community decision intelligence domains."""
    return {
        "domains": list_domains(),
        "total": len(list_domains()),
    }


@router.get("/snapshot")
async def get_snapshot(
    domain: str | None = Query(None, description="Filter to a single domain"),
):
    """Return a current-state metrics snapshot (live simulation or real connector)."""
    sim = get_simulator()
    if domain:
        metrics = sim.get_current_metrics(domain)
        if not metrics:
            raise HTTPException(status_code=404, detail=f"Domain '{domain}' not found")
        return {"domain": domain, "metrics": metrics}

    snapshot = sim.get_all_domains_snapshot()
    return {"snapshot": snapshot, "domains": list(snapshot.keys())}


@router.post("/forecast")
async def forecast_metric(req: ForecastRequest):
    """Forecast a community metric using linear-trend analysis."""
    try:
        sim = get_simulator()
        series = sim.get_time_series(
            req.domain,
            req.metric,
            days=req.historical_days,
        )
        if not series:
            raise HTTPException(
                status_code=404,
                detail=f"Metric '{req.metric}' not found in domain '{req.domain}'"
            )

        forecaster = get_forecaster()
        result = forecaster.forecast(
            series,
            horizon_days=req.horizon_days,
            metric_name=req.metric,
            domain=req.domain,
        )
        return result.to_dict()

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception("Forecast error")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/anomalies")
async def detect_anomalies(req: AnomalyRequest):
    """Detect anomalies in a community metric time series."""
    try:
        sim = get_simulator()
        series = sim.get_time_series(
            req.domain,
            req.metric,
            days=req.historical_days,
        )
        if not series:
            raise HTTPException(
                status_code=404,
                detail=f"Metric '{req.metric}' not found in domain '{req.domain}'"
            )

        detector = get_anomaly_detector()
        anomalies = detector.detect(series, metric_name=req.metric)
        return {
            "domain": req.domain,
            "metric": req.metric,
            "anomalies": [a.to_dict() for a in anomalies],
            "count": len(anomalies),
            "analyzed_points": len(series),
        }

    except Exception as e:
        logger.exception("Anomaly detection error")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insights/{domain}")
async def get_domain_insights(
    domain: str,
    max_insights: int = Query(3, ge=1, le=10),
):
    """Generate AI-driven insights for a community domain."""
    try:
        sim = get_simulator()
        metrics = sim.get_current_metrics(domain)
        if not metrics:
            raise HTTPException(status_code=404, detail=f"Domain '{domain}' not found")

        generator = get_insight_generator()
        insights = generator.generate(domain, metrics, max_insights=max_insights)
        return {
            "domain": domain,
            "insights": [i.to_dict() for i in insights],
            "metric_snapshot": metrics,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Insight generation error")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query")
async def domain_query(req: DomainQueryRequest):
    """
    Multi-agent domain-routed query.
    Auto-classifies the query domain, delegates to specialist agent,
    and returns enriched answer with recommendations and insights.
    """
    from karena.rag.pipeline import RAGPipeline
    from karena.domains.agents import CommunityDomain

    try:
        # Domain classification (auto or forced)
        if req.domain:
            try:
                domain_enum = CommunityDomain(req.domain)
            except ValueError:
                domain_enum = CommunityDomain.GENERAL
        else:
            domain_enum = classify_query(req.query)

        # RAG retrieval (reuse existing pipeline)
        pipeline = RAGPipeline()
        rag_result = await pipeline._query_async(
            req.query,
            session_id=req.session_id,
            user_id=req.user_id,
        )

        # Domain agent enrichment
        agent = get_domain_agent(domain_enum)
        domain_result = await agent.analyze(req.query, rag_result.sources)

        # Generate analytics insights
        sim = get_simulator()
        metrics = sim.get_current_metrics(domain_enum.value)
        gen = get_insight_generator()
        insights = gen.generate(domain_enum.value, metrics, max_insights=2)

        return {
            "answer": rag_result.answer,
            "domain": domain_enum.value,
            "domain_label": domain_enum.value.replace("_", " ").title(),
            "sources": rag_result.sources,
            "confidence": rag_result.confidence,
            "session_id": rag_result.session_id,
            "latency_ms": rag_result.latency_ms,
            "recommended_actions": domain_result.recommended_actions,
            "community_insights": [i.to_dict() for i in insights],
            "escalate_to_human": domain_result.escalate_to_human,
        }

    except Exception as e:
        logger.exception("Domain query error")
        raise HTTPException(status_code=500, detail=str(e))
