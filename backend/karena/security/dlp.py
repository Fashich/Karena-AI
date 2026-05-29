"""Karena AI Data Loss Prevention (DLP) Engine.

Provides comprehensive data protection through content inspection,
classification, and policy enforcement to prevent sensitive data leakage.
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DataSensitivity(str, Enum):
    """Data sensitivity levels."""

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class DLPAction(str, Enum):
    """Actions to take when DLP policy is violated."""

    ALLOW = "allow"
    REDACT = "redact"
    BLOCK = "block"
    ALERT = "alert"
    QUARANTINE = "quarantine"


@dataclass
class DLPPolicy:
    """DLP policy definition."""

    name: str
    description: str
    sensitivity_level: DataSensitivity
    patterns: list[str] = field(default_factory=list)
    actions: list[DLPAction] = field(default_factory=list)
    enabled: bool = True
    exceptions: list[str] = field(default_factory=list)


@dataclass
class DLPResult:
    """Result of DLP inspection."""

    is_compliant: bool
    sensitivity_level: DataSensitivity
    detected_patterns: list[dict[str, Any]] = field(default_factory=list)
    recommended_action: DLPAction = DLPAction.ALLOW
    redacted_content: str | None = None
    policy_violations: list[str] = field(default_factory=list)


class DLPEngine:
    """Data Loss Prevention engine for content inspection and policy enforcement."""

    def __init__(self) -> None:
        self.policies: dict[str, DLPPolicy] = {}
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns for performance."""
        self._compiled_patterns: dict[str, re.Pattern] = {}

    def register_policy(self, policy: DLPPolicy) -> None:
        """Register a DLP policy."""
        self.policies[policy.name] = policy
        for pattern in policy.patterns:
            try:
                self._compiled_patterns[f"{policy.name}:{pattern}"] = re.compile(
                    pattern, re.IGNORECASE
                )
            except re.error as e:
                raise ValueError(
                    f"Invalid regex pattern '{pattern}' in policy '{policy.name}': {e}"
                )

    def unregister_policy(self, policy_name: str) -> bool:
        """Unregister a DLP policy."""
        if policy_name in self.policies:
            del self.policies[policy_name]
            # Remove compiled patterns
            keys_to_remove = [k for k in self._compiled_patterns if k.startswith(f"{policy_name}:")]
            for key in keys_to_remove:
                del self._compiled_patterns[key]
            return True
        return False

    def inspect(self, content: str, context: dict[str, Any] | None = None) -> DLPResult:
        """Inspect content against all registered DLP policies."""
        context = context or {}
        detected_patterns = []
        policy_violations = []
        highest_sensitivity = DataSensitivity.PUBLIC
        sensitivity_order = [
            DataSensitivity.PUBLIC,
            DataSensitivity.INTERNAL,
            DataSensitivity.CONFIDENTIAL,
            DataSensitivity.RESTRICTED,
        ]

        for policy_name, policy in self.policies.items():
            if not policy.enabled:
                continue

            # Check for pattern matches
            for pattern_key, compiled_pattern in self._compiled_patterns.items():
                if not pattern_key.startswith(f"{policy_name}:"):
                    continue

                matches = list(compiled_pattern.finditer(content))
                if matches:
                    for match in matches:
                        detected_patterns.append(
                            {
                                "policy": policy_name,
                                "pattern": pattern_key,
                                "match": match.group(),
                                "start": match.start(),
                                "end": match.end(),
                                "sensitivity": policy.sensitivity_level.value,
                            }
                        )

                    # Update highest sensitivity
                    current_idx = sensitivity_order.index(highest_sensitivity)
                    new_idx = sensitivity_order.index(policy.sensitivity_level)
                    if new_idx > current_idx:
                        highest_sensitivity = policy.sensitivity_level

                    # Check for policy violation
                    if policy.actions and DLPAction.BLOCK in policy.actions:
                        policy_violations.append(
                            f"Policy '{policy_name}' violated: {policy.description}"
                        )

        # Determine recommended action
        recommended_action = DLPAction.ALLOW
        if policy_violations:
            recommended_action = DLPAction.BLOCK
        elif detected_patterns:
            if highest_sensitivity == DataSensitivity.RESTRICTED:
                recommended_action = DLPAction.REDACT
            elif highest_sensitivity == DataSensitivity.CONFIDENTIAL:
                recommended_action = DLPAction.ALERT

        # Generate redacted content if needed
        redacted_content = None
        if recommended_action == DLPAction.REDACT and detected_patterns:
            redacted_content = self._redact_content(content, detected_patterns)

        return DLPResult(
            is_compliant=len(policy_violations) == 0,
            sensitivity_level=highest_sensitivity,
            detected_patterns=detected_patterns,
            recommended_action=recommended_action,
            redacted_content=redacted_content,
            policy_violations=policy_violations,
        )

    def _redact_content(self, content: str, detections: list[dict]) -> str:
        """Redact sensitive content based on detections."""
        # Sort by position (reverse order to maintain indices)
        sorted_detections = sorted(detections, key=lambda x: x["start"], reverse=True)

        result = content
        for detection in sorted_detections:
            start = detection["start"]
            end = detection["end"]
            matched_text = detection["match"]
            # Replace with redaction marker
            redaction_marker = f"[REDACTED-{detection['sensitivity'].upper()}]"
            result = result[:start] + redaction_marker + result[end:]

        return result

    def classify_content(self, content: str) -> DataSensitivity:
        """Classify content sensitivity level."""
        result = self.inspect(content)
        return result.sensitivity_level

    def get_policies(self) -> list[DLPPolicy]:
        """Get all registered policies."""
        return list(self.policies.values())

    def get_policy(self, name: str) -> DLPPolicy | None:
        """Get a specific policy by name."""
        return self.policies.get(name)


# Pre-built DLP policies for common enterprise scenarios
def create_default_policies() -> list[DLPPolicy]:
    """Create default DLP policies for enterprise use."""
    return [
        DLPPolicy(
            name="credit_card_detection",
            description="Detect credit card numbers",
            sensitivity_level=DataSensitivity.CONFIDENTIAL,
            patterns=[
                r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b",
                r"\b(?:6(?:011|5[0-9]{2})[0-9]{12})\b",
            ],
            actions=[DLPAction.REDACT, DLPAction.ALERT],
        ),
        DLPPolicy(
            name="ssn_detection",
            description="Detect US Social Security Numbers",
            sensitivity_level=DataSensitivity.RESTRICTED,
            patterns=[r"\b\d{3}-\d{2}-\d{4}\b"],
            actions=[DLPAction.REDACT, DLPAction.BLOCK],
        ),
        DLPPolicy(
            name="email_detection",
            description="Detect email addresses",
            sensitivity_level=DataSensitivity.INTERNAL,
            patterns=[r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"],
            actions=[DLPAction.ALLOW],
        ),
        DLPPolicy(
            name="api_key_detection",
            description="Detect API keys and secrets",
            sensitivity_level=DataSensitivity.RESTRICTED,
            patterns=[
                r"(?i)(api[_-]?key|apikey)\s*[=:]\s*['\"]?[A-Za-z0-9_\-]{20,}['\"]?",
                r"(?i)(secret|token)\s*[=:]\s*['\"]?[A-Za-z0-9_\-]{20,}['\"]?",
            ],
            actions=[DLPAction.REDACT, DLPAction.BLOCK, DLPAction.ALERT],
        ),
    ]


# Global DLP engine instance
_dlp_engine: DLPEngine | None = None


def get_dlp_engine() -> DLPEngine:
    """Get or create the global DLP engine instance."""
    global _dlp_engine
    if _dlp_engine is None:
        _dlp_engine = DLPEngine()
        # Register default policies
        for policy in create_default_policies():
            _dlp_engine.register_policy(policy)
    return _dlp_engine
