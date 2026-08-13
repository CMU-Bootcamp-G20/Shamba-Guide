from __future__ import annotations

from typing import Protocol, Sequence

from shambaguide.schemas import (
    AdviceRequest,
    DraftActionPlan,
    EvidenceChunk,
    SafetyViolation,
    WeatherSnapshot,
)


class PlannerUnavailable(RuntimeError):
    """Raised when no local planning model is available."""


class Planner(Protocol):
    model_version: str

    def generate_plan(
        self,
        request: AdviceRequest,
        evidence: Sequence[EvidenceChunk],
        weather: WeatherSnapshot | None,
    ) -> DraftActionPlan:
        """Generate one JSON-schema-compatible draft plan."""

    def repair_plan(
        self,
        request: AdviceRequest,
        evidence: Sequence[EvidenceChunk],
        weather: WeatherSnapshot | None,
        previous_plan: DraftActionPlan,
        violations: Sequence[SafetyViolation],
    ) -> DraftActionPlan:
        """Generate one corrected plan from explicit safety feedback."""


class DisabledPlanner:
    """Safe default that prevents unsupported model-generated recommendations."""

    model_version = "not-configured"

    def generate_plan(
        self,
        request: AdviceRequest,
        evidence: Sequence[EvidenceChunk],
        weather: WeatherSnapshot | None,
    ) -> DraftActionPlan:
        del request, evidence, weather
        raise PlannerUnavailable("The local planning model is not connected.")

    def repair_plan(
        self,
        request: AdviceRequest,
        evidence: Sequence[EvidenceChunk],
        weather: WeatherSnapshot | None,
        previous_plan: DraftActionPlan,
        violations: Sequence[SafetyViolation],
    ) -> DraftActionPlan:
        del request, evidence, weather, previous_plan, violations
        raise PlannerUnavailable("The local planning model is not connected.")
