"""Karena AI A/B Testing Framework.

Provides comprehensive A/B testing capabilities for evaluating
feature changes, algorithm modifications, and UI adjustments.
"""

import hashlib
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class ExperimentStatus(str, Enum):
    """Experiment lifecycle status."""

    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class AssignmentStrategy(str, Enum):
    """Strategies for assigning users to treatments."""

    RANDOM = "random"
    HASH_BASED = "hash_based"
    WEIGHTED = "weighted"
    STRATIFIED = "stratified"


class MetricType(str, Enum):
    """Types of metrics tracked in experiments."""

    COUNTER = "counter"
    GAUGE = "gauge"
    RATE = "rate"
    PERCENTILE = "percentile"


@dataclass
class Treatment:
    """Represents a treatment variant in an experiment."""

    name: str
    description: str
    allocation_weight: float = 1.0
    config: dict[str, Any] = field(default_factory=dict)
    is_control: bool = False

    def __post_init__(self):
        if self.allocation_weight <= 0:
            raise ValueError("Allocation weight must be positive")


@dataclass
class ExperimentMetric:
    """Definition of a metric to track in an experiment."""

    name: str
    description: str
    metric_type: MetricType
    primary: bool = False
    target_direction: str = "higher"
    baseline_value: float | None = None
    min_detectable_effect: float | None = None


@dataclass
class UserAssignment:
    """Records a user's assignment to a treatment."""

    user_id: str
    experiment_id: str
    treatment_name: str
    assigned_at: str
    assignment_method: str
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricObservation:
    """Single observation of a metric."""

    user_id: str
    experiment_id: str
    treatment_name: str
    metric_name: str
    value: float
    timestamp: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExperimentResult:
    """Statistical results of an experiment."""

    experiment_id: str
    metric_name: str
    treatment_name: str
    control_name: str
    sample_size_treatment: int
    sample_size_control: int
    mean_treatment: float
    mean_control: float
    absolute_difference: float
    relative_difference: float
    p_value: float
    confidence_interval_lower: float
    confidence_interval_upper: float
    is_statistically_significant: bool
    confidence_level: float = 0.95


class ABTestingEngine:
    """A/B testing orchestration engine."""

    def __init__(self) -> None:
        self.experiments: dict[str, dict] = {}
        self.assignments: dict[str, UserAssignment] = {}
        self.observations: list[MetricObservation] = []

    def create_experiment(
        self,
        name: str,
        description: str,
        treatments: list[Treatment],
        metrics: list[ExperimentMetric],
        assignment_strategy: AssignmentStrategy = AssignmentStrategy.RANDOM,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        target_sample_size: int | None = None,
        hypothesis: str | None = None,
    ) -> str:
        """Create a new A/B test experiment."""
        experiment_id = f"exp_{uuid4().hex[:12]}"

        if not any(t.is_control for t in treatments):
            raise ValueError("At least one treatment must be marked as control")

        total_weight = sum(t.allocation_weight for t in treatments)

        experiment = {
            "experiment_id": experiment_id,
            "name": name,
            "description": description,
            "status": ExperimentStatus.DRAFT,
            "treatments": {t.name: t for t in treatments},
            "metrics": {m.name: m for m in metrics},
            "assignment_strategy": assignment_strategy,
            "start_time": start_time or datetime.now(timezone.utc),
            "end_time": end_time,
            "target_sample_size": target_sample_size,
            "hypothesis": hypothesis,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "total_weight": total_weight,
            "assignments_count": 0,
            "observations_count": 0,
        }

        self.experiments[experiment_id] = experiment
        return experiment_id

    def start_experiment(self, experiment_id: str) -> bool:
        """Start an experiment."""
        if experiment_id not in self.experiments:
            return False

        experiment = self.experiments[experiment_id]
        if experiment["status"] != ExperimentStatus.DRAFT:
            return False

        experiment["status"] = ExperimentStatus.RUNNING
        experiment["start_time"] = datetime.now(timezone.utc)
        return True

    def pause_experiment(self, experiment_id: str) -> bool:
        """Pause a running experiment."""
        if experiment_id not in self.experiments:
            return False

        experiment = self.experiments[experiment_id]
        if experiment["status"] != ExperimentStatus.RUNNING:
            return False

        experiment["status"] = ExperimentStatus.PAUSED
        return True

    def complete_experiment(self, experiment_id: str) -> bool:
        """Mark an experiment as completed."""
        if experiment_id not in self.experiments:
            return False

        experiment = self.experiments[experiment_id]
        experiment["status"] = ExperimentStatus.COMPLETED
        experiment["end_time"] = datetime.now(timezone.utc)
        return True

    def assign_user(
        self,
        experiment_id: str,
        user_id: str,
        context: dict[str, Any] | None = None,
    ) -> str | None:
        """Assign a user to a treatment group."""
        if experiment_id not in self.experiments:
            return None

        experiment = self.experiments[experiment_id]
        if experiment["status"] != ExperimentStatus.RUNNING:
            return None

        assignment_key = f"{experiment_id}:{user_id}"
        if assignment_key in self.assignments:
            return self.assignments[assignment_key].treatment_name

        strategy = experiment["assignment_strategy"]

        if strategy == AssignmentStrategy.HASH_BASED:
            treatment_name = self._assign_hash_based(experiment, user_id)
        elif strategy == AssignmentStrategy.WEIGHTED:
            treatment_name = self._assign_weighted(experiment)
        else:
            treatment_name = self._assign_random(experiment)

        assignment = UserAssignment(
            user_id=user_id,
            experiment_id=experiment_id,
            treatment_name=treatment_name,
            assigned_at=datetime.now(timezone.utc).isoformat(),
            assignment_method=strategy.value,
            context=context or {},
        )

        self.assignments[assignment_key] = assignment
        experiment["assignments_count"] += 1

        return treatment_name

    def _assign_random(self, experiment: dict) -> str:
        """Random assignment."""
        treatments = list(experiment["treatments"].values())
        return random.choice(treatments).name

    def _assign_hash_based(self, experiment: dict, user_id: str) -> str:
        """Hash-based deterministic assignment."""
        treatments = list(experiment["treatments"].values())
        total_weight = experiment["total_weight"]

        hash_input = f"{user_id}:{experiment['experiment_id']}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        normalized = (hash_value % 1000) / 1000.0

        cumulative = 0.0
        for treatment in treatments:
            weight_ratio = treatment.allocation_weight / total_weight
            cumulative += weight_ratio
            if normalized < cumulative:
                return treatment.name

        return treatments[-1].name

    def _assign_weighted(self, experiment: dict) -> str:
        """Weighted random assignment."""
        treatments = list(experiment["treatments"].values())
        weights = [t.allocation_weight for t in treatments]
        names = [t.name for t in treatments]
        return random.choices(names, weights=weights, k=1)[0]

    def record_metric(
        self,
        user_id: str,
        experiment_id: str,
        metric_name: str,
        value: float,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Record a metric observation."""
        if experiment_id not in self.experiments:
            return False

        if metric_name not in self.experiments[experiment_id]["metrics"]:
            return False

        assignment_key = f"{experiment_id}:{user_id}"
        if assignment_key not in self.assignments:
            return False

        assignment = self.assignments[assignment_key]

        observation = MetricObservation(
            user_id=user_id,
            experiment_id=experiment_id,
            treatment_name=assignment.treatment_name,
            metric_name=metric_name,
            value=value,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata=metadata or {},
        )

        self.observations.append(observation)
        self.experiments[experiment_id]["observations_count"] += 1

        return True

    def analyze_experiment(
        self,
        experiment_id: str,
        metric_name: str | None = None,
        confidence_level: float = 0.95,
    ) -> list[ExperimentResult]:
        """Analyze experiment results."""
        if experiment_id not in self.experiments:
            return []

        experiment = self.experiments[experiment_id]
        metrics_to_analyze = [metric_name] if metric_name else list(experiment["metrics"].keys())

        results = []

        for metric in metrics_to_analyze:
            if metric not in experiment["metrics"]:
                continue

            observations_by_treatment: dict[str, list[float]] = {}

            for obs in self.observations:
                if obs.experiment_id != experiment_id or obs.metric_name != metric:
                    continue

                if obs.treatment_name not in observations_by_treatment:
                    observations_by_treatment[obs.treatment_name] = []
                observations_by_treatment[obs.treatment_name].append(obs.value)

            control_data = None
            treatment_datas = []

            for treatment_name, values in observations_by_treatment.items():
                treatment = experiment["treatments"][treatment_name]
                if treatment.is_control:
                    control_data = (treatment_name, values)
                else:
                    treatment_datas.append((treatment_name, values))

            if not control_data:
                continue

            control_name, control_values = control_data

            for treatment_name, treatment_values in treatment_datas:
                result = self._calculate_statistics(
                    experiment_id=experiment_id,
                    metric_name=metric,
                    treatment_name=treatment_name,
                    control_name=control_name,
                    treatment_values=treatment_values,
                    control_values=control_values,
                    confidence_level=confidence_level,
                )

                if result:
                    results.append(result)

        return results

    def _calculate_statistics(
        self,
        experiment_id: str,
        metric_name: str,
        treatment_name: str,
        control_name: str,
        treatment_values: list[float],
        control_values: list[float],
        confidence_level: float = 0.95,
    ) -> ExperimentResult | None:
        """Calculate statistical significance."""
        if len(treatment_values) < 2 or len(control_values) < 2:
            return None

        mean_t = sum(treatment_values) / len(treatment_values)
        mean_c = sum(control_values) / len(control_values)

        var_t = sum((x - mean_t) ** 2 for x in treatment_values) / (len(treatment_values) - 1)
        var_c = sum((x - mean_c) ** 2 for x in control_values) / (len(control_values) - 1)

        se = ((var_t / len(treatment_values)) + (var_c / len(control_values))) ** 0.5

        if se == 0:
            return None

        t_stat = (mean_t - mean_c) / se
        p_value = 2 * (1 - min(0.5 * (1 + abs(t_stat) / (1 + abs(t_stat))), 0.9999))

        z_score = 1.96 if confidence_level == 0.95 else 2.576
        margin = z_score * se

        abs_diff = mean_t - mean_c
        rel_diff = (abs_diff / mean_c * 100) if mean_c != 0 else 0

        return ExperimentResult(
            experiment_id=experiment_id,
            metric_name=metric_name,
            treatment_name=treatment_name,
            control_name=control_name,
            sample_size_treatment=len(treatment_values),
            sample_size_control=len(control_values),
            mean_treatment=mean_t,
            mean_control=mean_c,
            absolute_difference=abs_diff,
            relative_difference=rel_diff,
            p_value=p_value,
            confidence_interval_lower=abs_diff - margin,
            confidence_interval_upper=abs_diff + margin,
            is_statistically_significant=p_value < (1 - confidence_level),
            confidence_level=confidence_level,
        )

    def get_experiment_status(self, experiment_id: str) -> dict[str, Any]:
        """Get current experiment status."""
        if experiment_id not in self.experiments:
            return {}

        exp = self.experiments[experiment_id]

        return {
            "experiment_id": experiment_id,
            "name": exp["name"],
            "status": exp["status"].value,
            "assignments_count": exp["assignments_count"],
            "observations_count": exp["observations_count"],
            "treatments": [
                {
                    "name": t.name,
                    "is_control": t.is_control,
                    "allocation_weight": t.allocation_weight,
                }
                for t in exp["treatments"].values()
            ],
            "metrics": [
                {"name": m.name, "primary": m.primary, "type": m.metric_type.value}
                for m in exp["metrics"].values()
            ],
        }


_ab_engine: ABTestingEngine | None = None


def get_ab_engine() -> ABTestingEngine:
    """Get or create the global A/B testing engine."""
    global _ab_engine
    if _ab_engine is None:
        _ab_engine = ABTestingEngine()
    return _ab_engine
