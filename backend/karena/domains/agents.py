"""
Community Decision Intelligence — Domain Specialist Agents.

Each agent is a deep-context expert for a community domain.
Architecture is Google ADK-compatible: swap `generate` for ADK tool calls.

Domains:
  - Urban Mobility & Transportation
  - Healthcare & Community Wellness
  - Environmental Sustainability
  - Citizen Services & Engagement
  - Disaster Response & Recovery
  - Education & Lifelong Learning
  - Energy & Smart Utilities
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class CommunityDomain(str, Enum):
    URBAN_MOBILITY = "urban_mobility"
    HEALTHCARE = "healthcare"
    ENVIRONMENT = "environment"
    CITIZEN_SERVICES = "citizen_services"
    DISASTER_RESPONSE = "disaster_response"
    EDUCATION = "education"
    ENERGY_UTILITIES = "energy_utilities"
    GENERAL = "general"


@dataclass
class DomainInsight:
    domain: CommunityDomain
    title: str
    summary: str
    recommendation: str
    confidence: float
    severity: str = "info"       # info | warning | critical
    data_sources: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass
class DomainQueryResult:
    answer: str
    domain: CommunityDomain
    insights: list[DomainInsight]
    recommended_actions: list[str]
    confidence: float
    escalate_to_human: bool = False


class DomainClassifier:
    """
    Classifies a query into the most relevant community domain.
    ADK-ready: can be replaced with Gemini function-calling classification.
    """

    DOMAIN_KEYWORDS: dict[CommunityDomain, list[str]] = {
        CommunityDomain.URBAN_MOBILITY: [
            "traffic", "transport", "bus", "train", "commute", "road",
            "congestion", "transit", "vehicle", "parking", "mobility",
            "route", "highway", "bicycle", "pedestrian", "infrastructure",
        ],
        CommunityDomain.HEALTHCARE: [
            "health", "hospital", "clinic", "doctor", "patient", "medical",
            "disease", "vaccination", "wellness", "ambulance", "emergency",
            "mental health", "nutrition", "medicine", "epidemic", "outbreak",
        ],
        CommunityDomain.ENVIRONMENT: [
            "air quality", "pollution", "carbon", "emission", "climate",
            "water", "waste", "recycling", "sustainability", "green",
            "temperature", "flood", "drought", "biodiversity", "ecosystem",
            "aqi", "pm2.5", "noise pollution",
        ],
        CommunityDomain.CITIZEN_SERVICES: [
            "permit", "license", "complaint", "report", "citizen", "service",
            "government", "policy", "regulation", "public", "community",
            "feedback", "petition", "engagement", "participation", "digital",
        ],
        CommunityDomain.DISASTER_RESPONSE: [
            "disaster", "emergency", "evacuation", "rescue", "relief",
            "earthquake", "typhoon", "cyclone", "fire", "landslide",
            "alert", "warning", "preparedness", "recovery", "resilience",
        ],
        CommunityDomain.EDUCATION: [
            "school", "student", "teacher", "learning", "curriculum",
            "literacy", "enrollment", "attendance", "exam", "university",
            "vocational", "skill", "training", "dropout", "performance",
        ],
        CommunityDomain.ENERGY_UTILITIES: [
            "energy", "electricity", "power", "grid", "solar", "renewable",
            "utility", "water supply", "sewage", "outage", "consumption",
            "efficiency", "smart meter", "battery", "generation",
        ],
    }

    def classify(self, query: str) -> CommunityDomain:
        """Return the domain with the most keyword matches."""
        q = query.lower()
        scores: dict[CommunityDomain, int] = {d: 0 for d in CommunityDomain}

        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            for kw in keywords:
                if kw in q:
                    scores[domain] += 1

        best = max(scores, key=lambda d: scores[d])
        return best if scores[best] > 0 else CommunityDomain.GENERAL


class BaseDomainAgent:
    """Base class for all domain agents."""

    domain: CommunityDomain
    system_context: str = ""
    kpi_metrics: list[str] = []

    async def analyze(self, query: str, retrieved_docs: list[dict]) -> DomainQueryResult:
        """
        Perform domain-specific analysis on retrieved documents.
        Subclasses extend this with domain expertise.
        """
        insights = self._extract_insights(retrieved_docs)
        actions = self._recommend_actions(query, retrieved_docs)
        answer = self._synthesize_answer(query, retrieved_docs)
        confidence = min(0.95, 0.5 + len(retrieved_docs) * 0.05)

        return DomainQueryResult(
            answer=answer,
            domain=self.domain,
            insights=insights,
            recommended_actions=actions,
            confidence=confidence,
            escalate_to_human=confidence < 0.55,
        )

    def _extract_insights(self, docs: list[dict]) -> list[DomainInsight]:
        if not docs:
            return []
        return [
            DomainInsight(
                domain=self.domain,
                title=f"Analysis: {doc.get('source_title', 'Document')}",
                summary=str(doc.get("text", ""))[:200],
                recommendation=f"Review {doc.get('source_title', 'this document')} for actionable steps.",
                confidence=float(doc.get("score", 0.7)),
                data_sources=[str(doc.get("source_id", ""))],
            )
            for doc in docs[:3]
        ]

    def _recommend_actions(self, query: str, docs: list[dict]) -> list[str]:
        return [
            f"Review {len(docs)} retrieved knowledge sources for evidence-based decision",
            "Cross-validate with real-time sensor data before acting",
            "Engage relevant stakeholders for implementation",
        ]

    def _synthesize_answer(self, query: str, docs: list[dict]) -> str:
        if not docs:
            return (
                f"[{self.domain.value.replace('_', ' ').title()} Agent] "
                "No specific documents found. Please upload domain-relevant data "
                "or configure real-time data connectors."
            )
        excerpts = "\n".join(f"- {d.get('text', '')[:150]}" for d in docs[:3])
        return (
            f"[{self.domain.value.replace('_', ' ').title()} Intelligence]\n\n"
            f"Based on {len(docs)} retrieved sources:\n{excerpts}\n\n"
            f"Query: {query}\n\n"
            "Configure an LLM provider (GOOGLE_API_KEY or OPENAI_API_KEY) for full synthesis."
        )


class UrbanMobilityAgent(BaseDomainAgent):
    domain = CommunityDomain.URBAN_MOBILITY
    system_context = """You are an urban mobility intelligence expert.
    You analyze traffic patterns, public transit efficiency, road safety,
    and multi-modal transport integration for APAC cities. You provide
    data-driven recommendations to reduce congestion, improve public
    transit, and make cities more walkable and cycle-friendly."""
    kpi_metrics = [
        "average_commute_time_minutes",
        "public_transit_ridership",
        "traffic_congestion_index",
        "road_incident_count",
        "ev_adoption_rate",
    ]

    def _recommend_actions(self, query: str, docs: list[dict]) -> list[str]:
        return [
            "Deploy adaptive traffic signal control on identified bottleneck corridors",
            "Increase bus frequency on high-demand routes during peak hours",
            "Implement park-and-ride facilities at transit hubs",
            "Launch real-time journey planner integration with public transit API",
            "Analyse first/last mile connectivity gaps with geospatial data",
        ]


class HealthcareAgent(BaseDomainAgent):
    domain = CommunityDomain.HEALTHCARE
    system_context = """You are a community health intelligence analyst.
    You monitor hospital capacity, disease surveillance, vaccination coverage,
    mental health trends, and healthcare accessibility across diverse communities.
    You help health authorities make proactive, evidence-based decisions."""
    kpi_metrics = [
        "hospital_bed_occupancy_rate",
        "average_er_wait_time_minutes",
        "active_disease_cases",
        "vaccination_coverage_pct",
        "mental_health_referral_rate",
    ]

    def _recommend_actions(self, query: str, docs: list[dict]) -> list[str]:
        return [
            "Activate surge capacity protocols if bed occupancy exceeds 85%",
            "Deploy mobile health units to underserved communities",
            "Accelerate vaccination outreach in low-coverage zones",
            "Strengthen disease surveillance with syndromic reporting",
            "Partner with telehealth providers to reduce ER overcrowding",
        ]


class EnvironmentAgent(BaseDomainAgent):
    domain = CommunityDomain.ENVIRONMENT
    system_context = """You are an environmental intelligence specialist.
    You analyse air quality indices, water quality, carbon emissions,
    climate resilience, biodiversity, and resource consumption patterns
    for APAC communities. You support evidence-based environmental policy."""
    kpi_metrics = [
        "air_quality_index",
        "water_quality_score",
        "carbon_emissions_mt",
        "green_space_coverage_pct",
        "plastic_waste_recycled_pct",
    ]

    def _recommend_actions(self, query: str, docs: list[dict]) -> list[str]:
        return [
            "Issue public health advisory if AQI exceeds 100 (Unhealthy for Sensitive Groups)",
            "Deploy additional air quality sensors in identified pollution hotspots",
            "Accelerate green infrastructure (parks, urban forests) in high-density areas",
            "Implement source-reduction policies targeting top emission contributors",
            "Expand water quality monitoring with IoT sensors in distribution network",
        ]


class CitizenServicesAgent(BaseDomainAgent):
    domain = CommunityDomain.CITIZEN_SERVICES
    system_context = """You are a citizen engagement and public services expert.
    You analyse service request volumes, resolution times, citizen satisfaction,
    digital adoption, and participatory governance for smart city operations.
    You help governments become more responsive and citizen-centric."""
    kpi_metrics = [
        "open_service_requests",
        "average_resolution_days",
        "citizen_satisfaction_score",
        "digital_adoption_rate",
        "participation_rate",
    ]

    def _recommend_actions(self, query: str, docs: list[dict]) -> list[str]:
        return [
            "Automate triage for the top 3 high-volume service request categories",
            "Launch proactive status notifications via WhatsApp/SMS to reduce call volume",
            "Deploy AI chatbot for first-response citizen queries (24/7 coverage)",
            "Establish SLA dashboards visible to citizens for full transparency",
            "Run targeted digital literacy programmes for low-adoption communities",
        ]


class DisasterResponseAgent(BaseDomainAgent):
    domain = CommunityDomain.DISASTER_RESPONSE
    system_context = """You are a disaster risk and emergency management specialist.
    You monitor active incidents, resource deployment, early warning signals,
    evacuation readiness, and community resilience for APAC disaster-prone regions.
    You support coordinated, life-saving emergency response decisions."""
    kpi_metrics = [
        "active_incidents",
        "resources_deployed_pct",
        "early_warning_alerts",
        "evacuation_readiness_score",
        "recovery_rate_pct",
    ]

    def _recommend_actions(self, query: str, docs: list[dict]) -> list[str]:
        return [
            "Activate Emergency Operations Centre if incident severity reaches Level 3",
            "Pre-position resources in zones flagged by predictive risk models",
            "Disseminate early warning through multi-channel broadcast (SMS, radio, sirens)",
            "Coordinate inter-agency resource sharing via centralised command platform",
            "Deploy community volunteers for last-mile evacuation in high-risk zones",
        ]


class EducationAgent(BaseDomainAgent):
    domain = CommunityDomain.EDUCATION
    system_context = """You are an education analytics and lifelong learning expert.
    You analyse school enrolment, attendance patterns, learning outcomes,
    teacher effectiveness, and infrastructure utilisation across diverse communities.
    You help education authorities improve equity and quality of learning."""
    kpi_metrics = [
        "school_enrolment_rate",
        "daily_attendance_rate",
        "learning_outcome_score",
        "teacher_student_ratio",
        "digital_learning_adoption",
    ]

    def _recommend_actions(self, query: str, docs: list[dict]) -> list[str]:
        return [
            "Target attendance intervention for schools below 80% daily attendance",
            "Deploy learning analytics to identify at-risk students early",
            "Expand STEM resources to underperforming districts",
            "Launch teacher professional development programme in flagged areas",
            "Provide conditional cash transfers to reduce dropout in vulnerable communities",
        ]


class EnergyUtilitiesAgent(BaseDomainAgent):
    domain = CommunityDomain.ENERGY_UTILITIES
    system_context = """You are an energy and smart utilities intelligence analyst.
    You monitor grid load, renewable energy penetration, power outages,
    water supply efficiency, and utility consumption patterns for smart communities.
    You support the transition to resilient, sustainable utility infrastructure."""
    kpi_metrics = [
        "grid_load_pct",
        "renewable_share_pct",
        "power_outages_count",
        "water_supply_efficiency_pct",
        "energy_per_capita_kwh",
    ]

    def _recommend_actions(self, query: str, docs: list[dict]) -> list[str]:
        return [
            "Activate demand response programmes if grid load exceeds 90%",
            "Fast-track rooftop solar installation in high-consumption residential zones",
            "Deploy smart meters for real-time consumption analytics and billing",
            "Inspect and repair water distribution network in low-efficiency segments",
            "Implement time-of-use tariffs to shift peak load to off-peak hours",
        ]


# ────────────────────────────────────────────────────────────────
# Registry & Factory
# ────────────────────────────────────────────────────────────────

_AGENT_REGISTRY: dict[CommunityDomain, type[BaseDomainAgent]] = {
    CommunityDomain.URBAN_MOBILITY: UrbanMobilityAgent,
    CommunityDomain.HEALTHCARE: HealthcareAgent,
    CommunityDomain.ENVIRONMENT: EnvironmentAgent,
    CommunityDomain.CITIZEN_SERVICES: CitizenServicesAgent,
    CommunityDomain.DISASTER_RESPONSE: DisasterResponseAgent,
    CommunityDomain.EDUCATION: EducationAgent,
    CommunityDomain.ENERGY_UTILITIES: EnergyUtilitiesAgent,
    CommunityDomain.GENERAL: BaseDomainAgent,
}

_classifier = DomainClassifier()
_agent_instances: dict[CommunityDomain, BaseDomainAgent] = {}


def get_domain_agent(domain: CommunityDomain) -> BaseDomainAgent:
    """Return (and cache) a domain agent instance."""
    if domain not in _agent_instances:
        cls = _AGENT_REGISTRY.get(domain, BaseDomainAgent)
        instance = cls()
        instance.domain = domain  # type: ignore[assignment]
        _agent_instances[domain] = instance
    return _agent_instances[domain]


def classify_query(query: str) -> CommunityDomain:
    """Classify a natural-language query into a community domain."""
    return _classifier.classify(query)


def list_domains() -> list[dict[str, str]]:
    """Return metadata for all registered domains."""
    return [
        {
            "id": domain.value,
            "label": domain.value.replace("_", " ").title(),
            "agent": cls.__name__,
            "system_context": cls.system_context[:120] + "…",
            "kpi_metrics": ", ".join(cls.kpi_metrics),
        }
        for domain, cls in _AGENT_REGISTRY.items()
        if domain != CommunityDomain.GENERAL
    ]
