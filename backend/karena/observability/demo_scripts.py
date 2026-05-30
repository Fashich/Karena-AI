"""Demo scripts and executive validation protocols for APAC client engagements.

Provides pre-configured demonstration flows, PoC validation checklists,
and success metric dashboards for Karena AI client presentations.
"""

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class DemoScenario:
    """Pre-scripted demo scenario for client presentations."""

    id: str
    title: str
    description: str
    persona: str  # CTO, Operations Manager, Compliance Officer, Knowledge Worker
    industry: str  # Financial Services, Healthcare, Technology
    queries: list[str]
    expected_outcomes: list[str]
    success_criteria: dict[str, float]


@dataclass
class DemoSession:
    """Active demo session with metrics tracking."""

    id: str
    scenario: DemoScenario
    start_time: float
    end_time: float | None = None
    query_results: list[dict] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    stakeholder_feedback: dict[str, str] = field(default_factory=dict)


# Pre-configured demo scenarios for APAC markets
DEMO_SCENARIOS = {
    "financial_services_compliance": DemoScenario(
        id="fs_compliance_001",
        title="APAC Financial Services Compliance Query",
        description="Demonstrate compliance-aware knowledge retrieval for Singapore/HK regulatory requirements",  # noqa: E501
        persona="Compliance Officer",
        industry="Financial Services",
        queries=[
            "What is our data retention policy for APAC customers?",
            "How do we handle cross-border data transfers under PDPA?",
            "Show me the audit trail requirements for customer transactions",
        ],
        expected_outcomes=[
            "Sub-second retrieval of compliance policies",
            "Clear source citations with document references",
            "Confidence scores above 0.8 for regulatory queries",
        ],
        success_criteria={
            "latency_p95_ms": 1000,
            "min_confidence": 0.75,
            "source_citation_rate": 1.0,
        },
    ),
    "healthcare_clinical_support": DemoScenario(
        id="hc_clinical_001",
        title="Healthcare Clinical Knowledge Synthesis",
        description="Secure clinical knowledge retrieval for hospital networks in Australia/Thailand",  # noqa: E501
        persona="Knowledge Worker (Clinician)",
        industry="Healthcare",
        queries=[
            "What are the current treatment guidelines for type 2 diabetes?",
            "Show me drug interaction warnings for metformin and contrast dye",
            "What is our protocol for patient data privacy under HIPAA?",
        ],
        expected_outcomes=[
            "Accurate medical information with authoritative sources",
            "Privacy-preserving responses without PHI exposure",
            "Escalation offered for high-risk clinical decisions",
        ],
        success_criteria={
            "latency_p95_ms": 1500,
            "min_confidence": 0.85,
            "escalation_trigger_rate": 0.1,
        },
    ),
    "technical_architecture": DemoScenario(
        id="tech_arch_001",
        title="Enterprise Architecture Validation",
        description="CTO-level demonstration of reference architecture and scalability",
        persona="CTO",
        industry="Technology",
        queries=[
            "Describe the Karena AI reference architecture",
            "How does the system achieve 99.9% uptime SLA?",
            "Explain the hybrid retrieval mechanism and re-ranking pipeline",
            "What are the disaster recovery procedures?",
        ],
        expected_outcomes=[
            "Clear technical explanations with architectural diagrams",
            "SLA commitments with supporting infrastructure details",
            "Multi-region failover capabilities demonstrated",
        ],
        success_criteria={
            "latency_p95_ms": 800,
            "min_confidence": 0.80,
            "technical_accuracy_score": 0.9,
        },
    ),
    "operations_productivity": DemoScenario(
        id="ops_prod_001",
        title="Operations Team Productivity Boost",
        description="Day-to-day usability demonstration for operations managers",
        persona="Operations Manager",
        industry="BPO/Shared Services",
        queries=[
            "When should support queries be escalated to human agents?",
            "Show me the escalation workflow for priority 1 incidents",
            "What is our average MTTR target for L1 support?",
        ],
        expected_outcomes=[
            "30% reduction in time-to-answer vs manual search",
            "Seamless escalation handoff with full context",
            "Actionable playbooks and runbooks surfaced",
        ],
        success_criteria={
            "latency_p95_ms": 1000,
            "time_savings_percent": 30,
            "escalation_success_rate": 0.95,
        },
    ),
}


class DemoOrchestrator:
    """Orchestrates demo sessions with real-time metrics tracking."""

    def __init__(self) -> None:
        self.sessions: dict[str, DemoSession] = {}
        self._current_session: DemoSession | None = None

    def create_session(self, scenario_id: str) -> DemoSession:
        """Initialize a new demo session."""
        if scenario_id not in DEMO_SCENARIOS:
            raise ValueError(f"Unknown scenario: {scenario_id}")

        session_id = f"demo_{int(time.time())}"
        session = DemoSession(
            id=session_id,
            scenario=DEMO_SCENARIOS[scenario_id],
            start_time=time.time(),
        )
        self.sessions[session_id] = session
        self._current_session = session
        return session

    async def execute_query(
        self,
        query: str,
        rag_pipeline: Any,  # RAGPipeline instance
    ) -> dict:
        """Execute a demo query with full metrics capture."""
        if not self._current_session:
            raise RuntimeError("No active demo session")

        start = time.perf_counter()
        try:
            result = await rag_pipeline.query(query)
            latency_ms = (time.perf_counter() - start) * 1000

            query_result = {
                "query": query,
                "answer": result.answer,
                "sources": result.sources,
                "confidence": result.confidence,
                "latency_ms": round(latency_ms, 2),
                "timestamp": datetime.utcnow().isoformat(),
            }

            self._current_session.query_results.append(query_result)
            return query_result

        except Exception as e:
            error_result = {
                "query": query,
                "error": str(e),
                "latency_ms": round((time.perf_counter() - start) * 1000, 2),
                "timestamp": datetime.utcnow().isoformat(),
            }
            self._current_session.query_results.append(error_result)
            return error_result

    def calculate_metrics(self) -> dict[str, Any]:
        """Calculate aggregate metrics for current session."""
        if not self._current_session:
            return {}

        results = self._current_session.query_results
        successful = [r for r in results if "error" not in r]

        if not successful:
            return {"total_queries": len(results), "successful": 0}

        latencies = [r["latency_ms"] for r in successful]
        confidences = [r["confidence"] for r in successful]

        # Calculate percentiles
        latencies_sorted = sorted(latencies)
        p50_idx = int(len(latencies_sorted) * 0.5)
        p95_idx = int(len(latencies_sorted) * 0.95)

        metrics = {
            "total_queries": len(results),
            "successful_queries": len(successful),
            "success_rate": len(successful) / len(results) if results else 0,
            "latency_p50_ms": latencies_sorted[p50_idx] if latencies_sorted else 0,
            "latency_p95_ms": latencies_sorted[p95_idx] if latencies_sorted else 0,
            "latency_avg_ms": sum(latencies) / len(latencies) if latencies else 0,
            "confidence_avg": sum(confidences) / len(confidences) if confidences else 0,
            "confidence_min": min(confidences) if confidences else 0,
            "queries_with_sources": sum(1 for r in successful if r.get("sources")),
            "source_citation_rate": (
                sum(1 for r in successful if r.get("sources")) / len(successful)
                if successful
                else 0
            ),
        }

        # Check against success criteria
        criteria = self._current_session.scenario.success_criteria
        metrics["meets_latency_target"] = metrics["latency_p95_ms"] <= criteria.get(
            "latency_p95_ms", 1000
        )
        metrics["meets_confidence_target"] = metrics["confidence_min"] >= criteria.get(
            "min_confidence", 0.7
        )

        self._current_session.metrics = metrics
        return metrics

    def generate_demo_report(self) -> dict[str, Any]:
        """Generate comprehensive demo report for stakeholders."""
        if not self._current_session:
            return {}

        metrics = self.calculate_metrics()
        session = self._current_session

        report = {
            "demo_id": session.id,
            "scenario": {
                "title": session.scenario.title,
                "persona": session.scenario.persona,
                "industry": session.scenario.industry,
            },
            "execution_summary": {
                "start_time": datetime.fromtimestamp(session.start_time).isoformat(),
                "duration_seconds": (session.end_time or time.time()) - session.start_time,
                "total_queries": session.scenario.queries,
                "executed_queries": len(session.query_results),
            },
            "performance_metrics": metrics,
            "success_validation": {
                "criteria_met": all(
                    [
                        metrics.get("meets_latency_target", False),
                        metrics.get("meets_confidence_target", False),
                    ]
                ),
                "expected_outcomes": session.scenario.expected_outcomes,
            },
            "stakeholder_feedback": session.stakeholder_feedback,
            "recommendations": self._generate_recommendations(metrics),
        }

        return report

    def _generate_recommendations(self, metrics: dict) -> list[str]:
        """Generate improvement recommendations based on metrics."""
        recommendations = []

        if not metrics.get("meets_latency_target", True):
            recommendations.append(
                "Consider implementing additional caching layers or optimizing vector index for faster retrieval"  # noqa: E501
            )

        if metrics.get("confidence_min", 1.0) < 0.7:
            recommendations.append(
                "Review embedding model selection and re-ranking configuration to improve response confidence"  # noqa: E501
            )

        if metrics.get("source_citation_rate", 1.0) < 0.9:
            recommendations.append(
                "Ensure all responses include source citations for enterprise trust and auditability"  # noqa: E501
            )

        return recommendations

    def record_feedback(self, stakeholder: str, feedback: str) -> None:
        """Record stakeholder feedback during demo."""
        if self._current_session:
            self._current_session.stakeholder_feedback[stakeholder] = feedback

    def close_session(self) -> None:
        """Close the current demo session."""
        if self._current_session:
            self._current_session.end_time = time.time()
            self.calculate_metrics()
            self._current_session = None


# Executive presentation helpers
def generate_executive_slide_deck(scenario_id: str) -> list[dict]:
    """Generate slide content for executive presentation."""
    if scenario_id not in DEMO_SCENARIOS:
        return []

    scenario = DEMO_SCENARIOS[scenario_id]

    slides = [
        {
            "slide_number": 1,
            "title": "Karena AI Demo Overview",
            "content": {
                "scenario_title": scenario.title,
                "target_persona": scenario.persona,
                "industry_focus": scenario.industry,
                "key_objectives": scenario.expected_outcomes,
            },
        },
        {
            "slide_number": 2,
            "title": "Business Value Proposition",
            "content": {
                "pain_points_addressed": [
                    "Knowledge fragmentation across silos",
                    "Slow mean-time-to-resolution for support queries",
                    "Compliance and audit trail requirements",
                ],
                "quantified_benefits": [
                    "30% reduction in MTTR",
                    "40% acceleration in knowledge discovery",
                    "99.9% uptime SLA compliance",
                ],
            },
        },
        {
            "slide_number": 3,
            "title": "Technical Differentiators",
            "content": {
                "hybrid_retrieval": "Dense vectors + BM25 lexical fusion",
                "two_stage_reranking": "Cross-encoder scoring + LTR features",
                "multi_tier_caching": "L1 in-process + L2 Redis",
                "enterprise_security": "OAuth2/OIDC, RBAC, audit logging",
            },
        },
        {
            "slide_number": 4,
            "title": "Success Criteria & Validation",
            "content": {
                "performance_targets": scenario.success_criteria,
                "demo_queries": scenario.queries,
                "validation_checklist": [
                    "✓ Sub-second latency under load",
                    "✓ Authoritative source citations",
                    "✓ Confidence scores > 0.75",
                    "✓ Seamless escalation workflow",
                ],
            },
        },
        {
            "slide_number": 5,
            "title": "Next Steps & Rollout Plan",
            "content": {
                "pilot_phase": "4-week pilot with anonymized dataset",
                "production_deployment": "8-12 week phased rollout",
                "success_gates": [
                    "PoC validation sign-off",
                    "Security & compliance review",
                    "User acceptance testing",
                ],
            },
        },
    ]

    return slides


def get_demo_orchestrator() -> DemoOrchestrator:
    """Get demo orchestrator instance."""
    return DemoOrchestrator()


def list_available_scenarios() -> list[dict]:
    """List all available demo scenarios."""
    return [
        {
            "id": sid,
            "title": s.title,
            "persona": s.persona,
            "industry": s.industry,
            "query_count": len(s.queries),
        }
        for sid, s in DEMO_SCENARIOS.items()
    ]
