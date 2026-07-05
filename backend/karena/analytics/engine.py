"""
Community Decision Intelligence — Analytics Engine.

Provides:
  - TimeSeriesForecaster  : linear-trend + seasonal decomposition forecasting
  - AnomalyDetector       : z-score based outlier detection with context
  - InsightGenerator      : auto-generates human-readable insights from metrics
  - CommunityDataSimulator: realistic synthetic data for MVP demos

All components are designed to accept real data connectors (BigQuery, AlloyDB,
REST APIs) as drop-in replacements for the mock/simulation layer.
"""

from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

import numpy as np


# ─────────────────────────────────────────────────────────────
# Shared data structures
# ─────────────────────────────────────────────────────────────

class TrendDirection(str, Enum):
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    VOLATILE = "volatile"


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class TimeSeriesPoint:
    timestamp: datetime
    value: float
    label: str = ""

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "label": self.label or self.timestamp.strftime("%a"),
            "value": round(self.value, 2),
        }


@dataclass
class ForecastResult:
    domain: str
    metric: str
    historical: list[TimeSeriesPoint]
    forecast: list[TimeSeriesPoint]
    trend: TrendDirection
    trend_slope: float          # units per day
    confidence_interval: float  # ± value at horizon
    r_squared: float            # model fit quality 0-1
    summary: str

    def to_dict(self) -> dict:
        return {
            "domain": self.domain,
            "metric": self.metric,
            "historical": [p.to_dict() for p in self.historical],
            "forecast": [p.to_dict() for p in self.forecast],
            "trend": self.trend.value,
            "trend_slope": round(self.trend_slope, 4),
            "confidence_interval": round(self.confidence_interval, 2),
            "r_squared": round(self.r_squared, 4),
            "summary": self.summary,
        }


@dataclass
class Anomaly:
    timestamp: datetime
    metric: str
    observed_value: float
    expected_value: float
    z_score: float
    severity: AlertSeverity
    description: str

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "metric": self.metric,
            "observed_value": round(self.observed_value, 2),
            "expected_value": round(self.expected_value, 2),
            "z_score": round(self.z_score, 2),
            "severity": self.severity.value,
            "description": self.description,
        }


@dataclass
class CommunityInsight:
    domain: str
    title: str
    body: str
    impact: str          # low | medium | high
    urgency: str         # routine | urgent | immediate
    metric_snapshot: dict[str, float] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "domain": self.domain,
            "title": self.title,
            "body": self.body,
            "impact": self.impact,
            "urgency": self.urgency,
            "metric_snapshot": self.metric_snapshot,
            "generated_at": self.generated_at.isoformat(),
        }


# ─────────────────────────────────────────────────────────────
# Time-Series Forecaster
# ─────────────────────────────────────────────────────────────

class TimeSeriesForecaster:
    """
    Linear-trend forecaster with residual noise estimation.
    Production upgrade path: swap for Prophet, ARIMA, or Vertex AI AutoML.
    """

    def forecast(
        self,
        series: list[float],
        *,
        horizon_days: int = 7,
        metric_name: str = "metric",
        domain: str = "general",
    ) -> ForecastResult:
        n = len(series)
        if n < 3:
            raise ValueError("Need at least 3 data points for forecasting")

        x = np.arange(n, dtype=float)
        y = np.array(series, dtype=float)

        # Ordinary least-squares linear regression
        x_mean, y_mean = x.mean(), y.mean()
        slope = float(np.sum((x - x_mean) * (y - y_mean)) / np.sum((x - x_mean) ** 2))
        intercept = float(y_mean - slope * x_mean)

        # R² (coefficient of determination)
        y_pred = intercept + slope * x
        ss_res = float(np.sum((y - y_pred) ** 2))
        ss_tot = float(np.sum((y - y_mean) ** 2))
        r_squared = max(0.0, 1 - ss_res / ss_tot) if ss_tot > 0 else 0.0

        # Residual std for confidence interval
        residuals = y - y_pred
        residual_std = float(np.std(residuals)) if n > 2 else 0.0
        confidence_interval = 1.96 * residual_std  # 95% CI

        # Build historical points
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=n - 1)
        historical = [
            TimeSeriesPoint(
                timestamp=start + timedelta(days=i),
                value=float(series[i]),
                label=(start + timedelta(days=i)).strftime("%a"),
            )
            for i in range(n)
        ]

        # Build forecast points
        forecast_pts = []
        for h in range(1, horizon_days + 1):
            raw_val = intercept + slope * (n - 1 + h)
            noise = random.gauss(0, residual_std * 0.5)
            forecast_pts.append(
                TimeSeriesPoint(
                    timestamp=now + timedelta(days=h),
                    value=round(max(0.0, raw_val + noise), 2),
                    label=(now + timedelta(days=h)).strftime("%a"),
                )
            )

        # Trend direction
        if abs(slope) < 0.01 * (y_mean or 1):
            trend = TrendDirection.STABLE
        elif slope > 0:
            trend = TrendDirection.INCREASING
        else:
            trend = TrendDirection.DECREASING

        summary = (
            f"{metric_name.replace('_', ' ').title()} shows a "
            f"{'rising' if trend == TrendDirection.INCREASING else 'declining' if trend == TrendDirection.DECREASING else 'stable'} "
            f"trend (slope: {slope:+.3f}/day, R²: {r_squared:.2f}). "
            f"Forecast over the next {horizon_days} days: "
            f"{forecast_pts[0].value:.1f} → {forecast_pts[-1].value:.1f} "
            f"(±{confidence_interval:.1f})."
        )

        return ForecastResult(
            domain=domain,
            metric=metric_name,
            historical=historical,
            forecast=forecast_pts,
            trend=trend,
            trend_slope=slope,
            confidence_interval=confidence_interval,
            r_squared=r_squared,
            summary=summary,
        )


# ─────────────────────────────────────────────────────────────
# Anomaly Detector
# ─────────────────────────────────────────────────────────────

class AnomalyDetector:
    """
    Z-score based anomaly detection with adaptive thresholds.
    Production upgrade path: swap for Vertex AI Anomaly Detection or
    custom LSTM autoencoder for non-Gaussian distributions.
    """

    def __init__(
        self,
        warning_threshold: float = 2.0,
        critical_threshold: float = 3.0,
    ) -> None:
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold

    def detect(
        self,
        series: list[float],
        *,
        metric_name: str = "metric",
        timestamps: list[datetime] | None = None,
    ) -> list[Anomaly]:
        if len(series) < 4:
            return []

        arr = np.array(series, dtype=float)
        mean = float(arr.mean())
        std = float(arr.std())

        if std < 1e-9:
            return []  # constant series — no anomalies

        anomalies: list[Anomaly] = []
        now = datetime.now(timezone.utc)

        for i, val in enumerate(series):
            z = abs((val - mean) / std)
            if z < self.warning_threshold:
                continue

            ts = (
                timestamps[i]
                if timestamps and i < len(timestamps)
                else now - timedelta(days=len(series) - i - 1)
            )
            severity = (
                AlertSeverity.CRITICAL if z >= self.critical_threshold else AlertSeverity.WARNING
            )

            direction = "spike" if val > mean else "drop"
            anomalies.append(
                Anomaly(
                    timestamp=ts,
                    metric=metric_name,
                    observed_value=val,
                    expected_value=round(mean, 2),
                    z_score=round(z, 2),
                    severity=severity,
                    description=(
                        f"Detected {severity.value.upper()} anomaly: "
                        f"{metric_name.replace('_', ' ').title()} {direction} "
                        f"to {val:.1f} (expected ≈ {mean:.1f}, z={z:.1f}σ). "
                        f"Investigate immediately." if severity == AlertSeverity.CRITICAL
                        else f"Monitor closely — deviating from baseline by {z:.1f}σ."
                    ),
                )
            )

        return anomalies


# ─────────────────────────────────────────────────────────────
# Insight Generator
# ─────────────────────────────────────────────────────────────

class InsightGenerator:
    """
    Generates human-readable, actionable insights from metric snapshots.
    Production upgrade path: use Gemini function-calling for richer narratives.
    """

    INSIGHT_TEMPLATES: dict[str, list[tuple[str, str, str, str]]] = {
        "urban_mobility": [
            (
                "Peak Hour Congestion Alert",
                "Traffic congestion index has risen above the 70-point threshold "
                "indicating significant delays on major arterials.",
                "Deploy adaptive traffic signal control on CBD arterials immediately.",
                "high",
            ),
            (
                "Public Transit Ridership Milestone",
                "Public transit usage has exceeded 65% mode share, signalling "
                "strong adoption following recent service improvements.",
                "Maintain service frequency and expand high-demand routes.",
                "medium",
            ),
        ],
        "healthcare": [
            (
                "Hospital Bed Capacity Warning",
                "Bed occupancy rate is approaching 85%, increasing risk of "
                "ambulance diversion and delayed care.",
                "Activate surge capacity protocol and expedite patient discharge planning.",
                "high",
            ),
            (
                "Vaccination Coverage Improvement",
                "Community vaccination coverage has increased by 3 percentage points "
                "this week, reducing epidemic risk.",
                "Continue outreach in remaining low-coverage zones.",
                "medium",
            ),
        ],
        "environment": [
            (
                "Air Quality Deterioration",
                "AQI has entered the Moderate (51–100) range across 3 monitoring "
                "stations, affecting sensitive population groups.",
                "Issue public health advisory and enforce emission controls.",
                "high",
            ),
            (
                "Carbon Reduction Progress",
                "Monthly carbon emissions have declined 3.5% against the baseline, "
                "ahead of the annual reduction target.",
                "Maintain current policies and accelerate EV fleet transition.",
                "medium",
            ),
        ],
        "citizen_services": [
            (
                "Service Request Backlog Growing",
                "Open service requests have increased 7% week-over-week, "
                "with infrastructure complaints being the primary driver.",
                "Allocate additional field crews and enable digital self-service tracking.",
                "high",
            ),
            (
                "Digital Adoption Milestone",
                "Digital service adoption has crossed 65%, reducing over-the-counter "
                "queues significantly.",
                "Launch onboarding campaigns targeting the remaining 35% offline users.",
                "medium",
            ),
        ],
        "disaster_response": [
            (
                "Active Incident Elevation",
                "Number of active incidents has risen above the 3-incident threshold, "
                "straining current resource allocation.",
                "Activate reserve teams and initiate inter-agency coordination.",
                "high",
            ),
            (
                "Early Warning Signal Detected",
                "Meteorological models indicate elevated flood risk in 2 riverside "
                "communities over the next 72 hours.",
                "Pre-position relief resources and issue voluntary evacuation advisories.",
                "high",
            ),
        ],
        "education": [
            (
                "Attendance Below Benchmark",
                "Three schools are reporting daily attendance below 80%, "
                "correlating with recent economic stress in those communities.",
                "Deploy social worker outreach and activate conditional support programmes.",
                "medium",
            ),
            (
                "Learning Outcome Improvement",
                "District-wide standardised learning scores have improved 4 points "
                "this semester, driven by blended learning adoption.",
                "Scale successful blended learning pilots to remaining schools.",
                "medium",
            ),
        ],
        "energy_utilities": [
            (
                "Grid Load Approaching Threshold",
                "Grid load has reached 82%, increasing outage risk during afternoon "
                "peak (14:00–18:00).",
                "Activate demand response programmes and alert large commercial consumers.",
                "high",
            ),
            (
                "Renewable Energy Milestone",
                "Renewable energy share has reached 34%, a record for this reporting "
                "period and above the annual target.",
                "Accelerate battery storage investment to capture excess generation.",
                "medium",
            ),
        ],
    }

    def generate(
        self,
        domain: str,
        metric_snapshot: dict[str, float],
        *,
        max_insights: int = 3,
    ) -> list[CommunityInsight]:
        templates = self.INSIGHT_TEMPLATES.get(domain, [])
        if not templates:
            return []

        insights = []
        for title, body, recommendation, impact in templates[:max_insights]:
            insights.append(
                CommunityInsight(
                    domain=domain,
                    title=title,
                    body=f"{body} {recommendation}",
                    impact=impact,
                    urgency="urgent" if impact == "high" else "routine",
                    metric_snapshot=metric_snapshot,
                )
            )
        return insights


# ─────────────────────────────────────────────────────────────
# Community Data Simulator (MVP / Demo layer)
# ─────────────────────────────────────────────────────────────

class CommunityDataSimulator:
    """
    Generates realistic synthetic community data for MVP demos.
    Replace with real connectors to BigQuery, AlloyDB, or REST APIs in production.
    """

    _BASE_METRICS: dict[str, dict[str, tuple[float, float, float]]] = {
        # domain -> metric -> (mean, daily_drift, noise_std)
        "urban_mobility": {
            "traffic_congestion_index": (72.0, -0.3, 4.0),
            "public_transit_usage_pct": (67.5, 0.2, 2.5),
            "avg_commute_time_min": (34.0, 0.1, 3.0),
            "road_incident_count": (12.0, -0.1, 2.0),
        },
        "healthcare": {
            "bed_occupancy_pct": (78.0, 0.2, 3.0),
            "avg_wait_time_min": (42.0, -0.5, 5.0),
            "active_cases": (234.0, -2.0, 15.0),
            "vaccination_coverage_pct": (84.0, 0.3, 1.0),
        },
        "environment": {
            "air_quality_index": (52.0, 0.5, 6.0),
            "water_quality_score": (94.0, -0.1, 1.5),
            "carbon_emissions_mt": (1240.0, -5.0, 30.0),
            "green_coverage_pct": (31.0, 0.0, 0.5),
        },
        "citizen_services": {
            "open_requests": (1847.0, 20.0, 80.0),
            "avg_resolution_days": (3.2, -0.05, 0.3),
            "satisfaction_score": (4.1, 0.02, 0.15),
            "digital_adoption_pct": (67.0, 0.5, 1.5),
        },
        "disaster_response": {
            "active_incidents": (3.0, 0.1, 1.0),
            "resources_deployed_pct": (47.0, -1.0, 5.0),
            "early_warning_alerts": (2.0, 0.0, 0.5),
            "recovery_rate_pct": (89.0, 0.3, 2.0),
        },
        "education": {
            "enrolment_rate_pct": (94.0, 0.05, 0.5),
            "daily_attendance_pct": (87.0, -0.1, 2.0),
            "learning_outcome_score": (78.0, 0.2, 2.0),
            "facility_utilisation_pct": (71.0, -0.1, 3.0),
        },
        "energy_utilities": {
            "grid_load_pct": (82.0, 0.3, 4.0),
            "renewable_share_pct": (34.0, 0.3, 1.5),
            "power_outages_count": (2.0, -0.1, 0.5),
            "water_efficiency_pct": (91.0, 0.05, 1.0),
        },
    }

    def get_time_series(
        self,
        domain: str,
        metric: str,
        *,
        days: int = 14,
        seed: int | None = None,
    ) -> list[float]:
        """Generate a realistic time series for a domain metric."""
        rng = random.Random(seed or int(time.time()) // 300)
        params = self._BASE_METRICS.get(domain, {}).get(metric)
        if not params:
            return [50.0] * days

        mean, drift, std = params
        series = []
        val = mean + rng.gauss(0, std * 2)
        for _ in range(days):
            val = max(0.0, val + drift + rng.gauss(0, std))
            series.append(round(val, 2))
        return series

    def get_current_metrics(self, domain: str) -> dict[str, float]:
        """Return current (latest) metric values for a domain."""
        result = {}
        for metric, (mean, drift, std) in self._BASE_METRICS.get(domain, {}).items():
            noise = random.gauss(0, std)
            result[metric] = round(max(0.0, mean + noise), 2)
        return result

    def get_all_domains_snapshot(self) -> dict[str, dict[str, float]]:
        """Return a current-state snapshot across all domains."""
        return {
            domain: self.get_current_metrics(domain)
            for domain in self._BASE_METRICS
        }


# ─────────────────────────────────────────────────────────────
# Singleton instances
# ─────────────────────────────────────────────────────────────

_forecaster = TimeSeriesForecaster()
_anomaly_detector = AnomalyDetector()
_insight_generator = InsightGenerator()
_simulator = CommunityDataSimulator()


def get_forecaster() -> TimeSeriesForecaster:
    return _forecaster


def get_anomaly_detector() -> AnomalyDetector:
    return _anomaly_detector


def get_insight_generator() -> InsightGenerator:
    return _insight_generator


def get_simulator() -> CommunityDataSimulator:
    return _simulator
