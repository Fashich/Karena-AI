"""Long-term user profile memory for personalization.

Stores persistent user preferences, expertise levels, domain interests,
and behavioral patterns to enable adaptive response generation.
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ExpertiseLevel(str, Enum):
    """User expertise classification."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class CommunicationPreference(str, Enum):
    """Preferred communication style."""

    CONCISE = "concise"  # Brief, direct answers
    DETAILED = "detailed"  # Comprehensive explanations
    TECHNICAL = "technical"  # Technical jargon acceptable
    NON_TECHNICAL = "non_technical"  # Plain language preferred
    VISUAL = "visual"  # Prefer diagrams and structured formats


@dataclass
class DomainInterest:
    """User's interest in a specific domain."""

    domain: str
    interest_level: float  # 0.0 - 1.0
    last_interaction: float
    interaction_count: int = 0


@dataclass
class UserProfile:
    """Persistent user profile for personalization."""

    user_id: str
    tenant_id: str
    email: str
    created_at: float
    updated_at: float

    # Expertise and preferences
    expertise_level: ExpertiseLevel = ExpertiseLevel.INTERMEDIATE
    communication_preference: CommunicationPreference = CommunicationPreference.DETAILED

    # Domain interests (tracked dynamically)
    domain_interests: list[DomainInterest] = field(default_factory=list)

    # Behavioral patterns
    avg_query_length: float = 50.0
    preferred_response_length: int = 500  # tokens
    typical_session_duration: float = 300.0  # seconds
    escalation_rate: float = 0.1  # percentage of queries escalated

    # Satisfaction metrics
    avg_satisfaction_score: float = 0.8  # -1 to 1 scale
    total_interactions: int = 0
    positive_feedback_count: int = 0
    negative_feedback_count: int = 0

    # Privacy settings
    allow_personalization: bool = True
    allow_analytics: bool = True
    data_retention_days: int = 365

    # Custom metadata
    metadata: dict[str, Any] = field(default_factory=dict)


# In-memory user profile store (production: database)
_user_profiles: dict[str, UserProfile] = {}


class UserProfileStore:
    """Manages long-term user profiles for personalization."""

    def __init__(self) -> None:
        self._profiles = _user_profiles

    async def create_profile(
        self,
        user_id: str,
        tenant_id: str,
        email: str,
        expertise_level: ExpertiseLevel = ExpertiseLevel.INTERMEDIATE,
        communication_preference: CommunicationPreference = CommunicationPreference.DETAILED,
    ) -> UserProfile:
        """Create a new user profile."""
        now = time.time()

        profile = UserProfile(
            user_id=user_id,
            tenant_id=tenant_id,
            email=email,
            created_at=now,
            updated_at=now,
            expertise_level=expertise_level,
            communication_preference=communication_preference,
        )

        self._profiles[user_id] = profile
        return profile

    async def get_profile(self, user_id: str) -> UserProfile | None:
        """Retrieve user profile by ID."""
        return self._profiles.get(user_id)

    async def update_profile(
        self,
        user_id: str,
        **updates: Any,
    ) -> UserProfile | None:
        """Update user profile fields."""
        profile = self._profiles.get(user_id)
        if not profile:
            return None

        for key, value in updates.items():
            if hasattr(profile, key):
                setattr(profile, key, value)

        profile.updated_at = time.time()
        return profile

    async def track_interaction(
        self,
        user_id: str,
        query_length: int,
        response_length: int,
        session_duration: float,
        satisfaction_score: float | None = None,
        escalated: bool = False,
    ) -> None:
        """Track user interaction for behavioral pattern learning."""
        profile = self._profiles.get(user_id)
        if not profile:
            return

        profile.total_interactions += 1

        # Update running averages with exponential moving average
        alpha = 0.1  # Smoothing factor

        profile.avg_query_length = (1 - alpha) * profile.avg_query_length + alpha * query_length
        profile.preferred_response_length = int(
            (1 - alpha) * profile.preferred_response_length + alpha * response_length
        )
        profile.typical_session_duration = (
            1 - alpha
        ) * profile.typical_session_duration + alpha * session_duration

        if escalated:
            profile.escalation_rate = (1 - alpha) * profile.escalation_rate + alpha * 1.0
        else:
            profile.escalation_rate = (1 - alpha) * profile.escalation_rate + alpha * 0.0

        if satisfaction_score is not None:
            if satisfaction_score > 0:
                profile.positive_feedback_count += 1
            elif satisfaction_score < 0:
                profile.negative_feedback_count += 1

            profile.avg_satisfaction_score = (
                1 - alpha
            ) * profile.avg_satisfaction_score + alpha * satisfaction_score

        profile.updated_at = time.time()

    async def update_domain_interest(
        self,
        user_id: str,
        domain: str,
        interest_delta: float = 0.1,
    ) -> None:
        """Update user's interest level in a domain."""
        profile = self._profiles.get(user_id)
        if not profile:
            return

        now = time.time()

        # Find existing domain interest
        for interest in profile.domain_interests:
            if interest.domain == domain:
                interest.interest_level = min(1.0, interest.interest_level + interest_delta)
                interest.last_interaction = now
                interest.interaction_count += 1
                break
        else:
            # Add new domain interest
            profile.domain_interests.append(
                DomainInterest(
                    domain=domain,
                    interest_level=interest_delta,
                    last_interaction=now,
                    interaction_count=1,
                )
            )

        # Decay old interests
        for interest in profile.domain_interests:
            age_days = (now - interest.last_interaction) / 86400
            if age_days > 30:
                interest.interest_level *= 0.9

        profile.updated_at = now

    async def delete_profile(self, user_id: str) -> bool:
        """Delete user profile (GDPR right to be forgotten)."""
        if user_id in self._profiles:
            del self._profiles[user_id]
            return True
        return False

    async def export_user_data(self, user_id: str) -> dict[str, Any] | None:
        """Export all user data for GDPR compliance."""
        profile = self._profiles.get(user_id)
        if not profile:
            return None

        return {
            "user_id": profile.user_id,
            "email": profile.email,
            "tenant_id": profile.tenant_id,
            "created_at": profile.created_at,
            "profile_data": {
                "expertise_level": profile.expertise_level.value,
                "communication_preference": profile.communication_preference.value,
                "domain_interests": [
                    {
                        "domain": i.domain,
                        "interest_level": i.interest_level,
                        "interaction_count": i.interaction_count,
                    }
                    for i in profile.domain_interests
                ],
                "behavioral_patterns": {
                    "avg_query_length": profile.avg_query_length,
                    "preferred_response_length": profile.preferred_response_length,
                    "typical_session_duration": profile.typical_session_duration,
                    "escalation_rate": profile.escalation_rate,
                },
                "satisfaction_metrics": {
                    "avg_satisfaction_score": profile.avg_satisfaction_score,
                    "total_interactions": profile.total_interactions,
                    "positive_feedback_count": profile.positive_feedback_count,
                    "negative_feedback_count": profile.negative_feedback_count,
                },
            },
            "metadata": profile.metadata,
        }

    async def get_top_domains(self, user_id: str, limit: int = 5) -> list[str]:
        """Get user's top domains of interest."""
        profile = self._profiles.get(user_id)
        if not profile:
            return []

        sorted_interests = sorted(
            profile.domain_interests,
            key=lambda x: x.interest_level,
            reverse=True,
        )
        return [i.domain for i in sorted_interests[:limit]]

    async def personalize_prompt(
        self,
        user_id: str,
        base_prompt: str,
    ) -> str:
        """Adapt prompt based on user profile."""
        profile = self._profiles.get(user_id)
        if not profile or not profile.allow_personalization:
            return base_prompt

        # Adjust tone and detail level based on preferences
        pref_instructions = {
            CommunicationPreference.CONCISE: "Provide concise, direct answers.",
            CommunicationPreference.DETAILED: "Provide comprehensive, detailed explanations.",
            CommunicationPreference.TECHNICAL: "Use technical terminology appropriate for experts.",
            CommunicationPreference.NON_TECHNICAL: "Use plain language, avoid jargon.",
            CommunicationPreference.VISUAL: "Use structured formatting, lists,\n                 and clear organization.",
        }

        expertise_instructions = {
            ExpertiseLevel.BEGINNER: "Explain concepts from first principles.",
            ExpertiseLevel.INTERMEDIATE: "Assume some domain knowledge.",
            ExpertiseLevel.ADVANCED: "Assume strong domain knowledge.",
            ExpertiseLevel.EXPERT: "Focus on nuanced details and edge cases.",
        }

        instruction = (
            f"\n\nPersonalization for this user:\n"
            f"- Communication style: {
                pref_instructions.get(
                    profile.communication_preference, '')}\n"
            f"- Expertise level: {expertise_instructions.get(profile.expertise_level, '')}\n"
            f"- Preferred response length: ~{profile.preferred_response_length} tokens"
        )

        return base_prompt + instruction


# Global store instance
_store: UserProfileStore | None = None


def get_user_profile_store() -> UserProfileStore:
    """Get or create user profile store instance."""
    global _store
    if _store is None:
        _store = UserProfileStore()
    return _store
