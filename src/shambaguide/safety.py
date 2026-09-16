from __future__ import annotations

from datetime import UTC, datetime
from typing import Sequence

from shambaguide.schemas import (
    ActionCategory,
    DraftActionPlan,
    EvidenceChunk,
    SafetyViolation,
    WeatherSnapshot,
)

RAIN_SPRAY_RULE_ID = "CLIMATE-RAIN-SPRAY-001"
SPRAY_WEATHER_REQUIRED_RULE_ID = "CLIMATE-SPRAY-WEATHER-001"
STALE_WEATHER_RULE_ID = "CLIMATE-WEATHER-STALE-001"
SOURCE_REQUIRED_RULE_ID = "TRACE-SOURCE-REQUIRED-001"
UNKNOWN_SOURCE_RULE_ID = "TRACE-UNKNOWN-SOURCE-001"
EMPTY_PLAN_RULE_ID = "PLAN-EMPTY-001"

class SafetyEngine:
    """Deterministic validation applied after structured plan generation.

    The 0.70 rain threshold is the demonstration value stated in the project proposal.
    It must remain versioned and should be replaced only after domain approval.
    """

    def __init__(self, *, rain_spray_threshold: float = 0.70) -> None:
        self.rain_spray_threshold = rain_spray_threshold

    def evaluate(
        self,
        plan: DraftActionPlan,
        evidence: Sequence[EvidenceChunk],
        weather: WeatherSnapshot | None,
        *,
        now: datetime | None = None,
    ) -> list[SafetyViolation]:
        current_time = now or datetime.now(UTC)
        known_source_ids = {chunk.source_id for chunk in evidence}
        violations: list[SafetyViolation] = []

        if not plan.actions and not plan.requires_extension_officer:
            violations.append(
                SafetyViolation(
                    rule_id=EMPTY_PLAN_RULE_ID,
                    message="The plan contains no action and no escalation decision.",
                )
            )

        for action in plan.actions:
            if not action.source_ids:
                violations.append(
                    SafetyViolation(
                        rule_id=SOURCE_REQUIRED_RULE_ID,
                        action_id=action.action_id,
                        message="Every action must cite at least one retrieved source.",
                    )
                )
            else:
                unknown = sorted(set(action.source_ids) - known_source_ids)
                if unknown:
                    violations.append(
                        SafetyViolation(
                            rule_id=UNKNOWN_SOURCE_RULE_ID,
                            action_id=action.action_id,
                            message=(
                                "The action cites source IDs that were not retrieved: "
                                + ", ".join(unknown)
                            ),
                        )
                    )

            if action.category != ActionCategory.SPRAY:
                continue

            if weather is None:
                violations.append(
                    SafetyViolation(
                        rule_id=SPRAY_WEATHER_REQUIRED_RULE_ID,
                        action_id=action.action_id,
                        message=(
                            "Spraying is blocked because no current weather record "
                            "is available."
                        ),
                    )
                )
                continue

            if not (weather.valid_from <= current_time <= weather.valid_to):
                violations.append(
                    SafetyViolation(
                        rule_id=STALE_WEATHER_RULE_ID,
                        action_id=action.action_id,
                        message=(
                            "Spraying is blocked because the weather record is outside "
                            "its validity window."
                        ),
                    )
                )
                continue

            rain_probability = weather.rain_probability_6h
            if (
                rain_probability is not None
                and rain_probability > self.rain_spray_threshold
            ):
                violations.append(
                    SafetyViolation(
                        rule_id=RAIN_SPRAY_RULE_ID,
                        action_id=action.action_id,
                        message=(
                            "Spraying is blocked because the six-hour rain probability "
                            f"({rain_probability:.2f}) exceeds "
                            f"{self.rain_spray_threshold:.2f}."
                        ),
                    )
                )

        return violations
