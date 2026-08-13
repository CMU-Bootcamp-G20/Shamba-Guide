from __future__ import annotations

import uuid
from collections.abc import Sequence

from shambaguide.db import SQLiteStore
from shambaguide.model import Planner, PlannerUnavailable
from shambaguide.rag import Retriever
from shambaguide.safety import SafetyEngine
from shambaguide.schemas import (
    AdviceAction,
    AdviceRequest,
    AdviceResponse,
    AdviceStatus,
    DecisionReceipt,
    DraftActionPlan,
    EvidenceChunk,
    SafetyViolation,
    SourceReference,
    WeatherSnapshot,
)


class AdviceService:
    """Shared application service used by web, API, and future USSD adapters."""

    def __init__(
        self,
        *,
        store: SQLiteStore,
        retriever: Retriever,
        planner: Planner,
        safety: SafetyEngine,
        max_repair_attempts: int = 1,
    ) -> None:
        self.store = store
        self.retriever = retriever
        self.planner = planner
        self.safety = safety
        self.max_repair_attempts = max(0, max_repair_attempts)

    def build_advice(self, request: AdviceRequest) -> AdviceResponse:
        evidence = self.retriever.retrieve(request, top_k=5)
        weather = self.store.get_current_weather(
            district=request.district,
            sector=request.sector,
        )

        if not evidence:
            return self._finalize(
                request,
                AdviceResponse(
                    receipt_id=_new_receipt_id(),
                    status=AdviceStatus.ABSTAINED,
                    message=(
                        "No reviewed local evidence is available for this question. "
                        "Please consult an extension officer."
                    ),
                    warnings=[
                        "The system did not generate an unsupported recommendation."
                    ],
                    weather_record_id=weather.record_id if weather else None,
                    model_version=self.planner.model_version,
                ),
            )

        try:
            plan = self.planner.generate_plan(request, evidence, weather)
        except PlannerUnavailable:
            return self._finalize(
                request,
                AdviceResponse(
                    receipt_id=_new_receipt_id(),
                    status=AdviceStatus.ABSTAINED,
                    message=(
                        "Reviewed evidence was retrieved, but the local planning model "
                        "is not connected yet."
                    ),
                    sources=_source_references(evidence),
                    weather_record_id=weather.record_id if weather else None,
                    model_version=self.planner.model_version,
                ),
            )

        violations = self.safety.evaluate(plan, evidence, weather)
        applied_rule_ids = _unique_rule_ids(violations)
        original_warnings = [violation.message for violation in violations]

        if violations and self.max_repair_attempts > 0:
            try:
                repaired_plan = self.planner.repair_plan(
                    request,
                    evidence,
                    weather,
                    plan,
                    violations,
                )
            except PlannerUnavailable:
                repaired_plan = None

            if repaired_plan is not None:
                repaired_violations = self.safety.evaluate(
                    repaired_plan,
                    evidence,
                    weather,
                )
                applied_rule_ids = _unique_rule_ids(
                    [*violations, *repaired_violations]
                )
                if not repaired_violations:
                    return self._finalize(
                        request,
                        self._response_from_plan(
                            repaired_plan,
                            evidence=evidence,
                            weather=weather,
                            status=AdviceStatus.REPAIRED,
                            applied_rule_ids=applied_rule_ids,
                            extra_warnings=original_warnings,
                        ),
                    )
                violations = repaired_violations

        if violations:
            return self._finalize(
                request,
                AdviceResponse(
                    receipt_id=_new_receipt_id(),
                    status=AdviceStatus.BLOCKED,
                    message=(
                        "The draft recommendation was blocked by deterministic safety "
                        "validation. Please consult an extension officer."
                    ),
                    warnings=[violation.message for violation in violations],
                    sources=_source_references(evidence),
                    applied_rule_ids=applied_rule_ids,
                    weather_record_id=weather.record_id if weather else None,
                    model_version=self.planner.model_version,
                ),
            )

        status = (
            AdviceStatus.ABSTAINED
            if plan.requires_extension_officer
            else AdviceStatus.APPROVED
        )
        return self._finalize(
            request,
            self._response_from_plan(
                plan,
                evidence=evidence,
                weather=weather,
                status=status,
                applied_rule_ids=applied_rule_ids,
            ),
        )

    def get_receipt(self, receipt_id: str) -> DecisionReceipt | None:
        return self.store.get_receipt(receipt_id)

    def _response_from_plan(
        self,
        plan: DraftActionPlan,
        *,
        evidence: Sequence[EvidenceChunk],
        weather: WeatherSnapshot | None,
        status: AdviceStatus,
        applied_rule_ids: list[str],
        extra_warnings: Sequence[str] = (),
    ) -> AdviceResponse:
        return AdviceResponse(
            receipt_id=_new_receipt_id(),
            status=status,
            message=plan.summary,
            actions=[
                AdviceAction(
                    action_id=action.action_id,
                    category=action.category,
                    text=action.instruction,
                    timeframe=action.timeframe,
                    reason=action.reason,
                    source_ids=action.source_ids,
                )
                for action in plan.actions
            ],
            warnings=[*extra_warnings, *plan.warnings],
            sources=_source_references(evidence),
            applied_rule_ids=applied_rule_ids,
            weather_record_id=weather.record_id if weather else None,
            model_version=self.planner.model_version,
        )

    def _finalize(
        self,
        request: AdviceRequest,
        response: AdviceResponse,
    ) -> AdviceResponse:
        self.store.save_receipt(request, response)
        return response


def _new_receipt_id() -> str:
    return f"receipt-{uuid.uuid4().hex[:16]}"


def _source_references(evidence: Sequence[EvidenceChunk]) -> list[SourceReference]:
    return [
        SourceReference(
            source_id=chunk.source_id,
            title=chunk.title,
            page=chunk.page,
            section=chunk.section,
        )
        for chunk in evidence
    ]


def _unique_rule_ids(violations: Sequence[SafetyViolation]) -> list[str]:
    return list(dict.fromkeys(violation.rule_id for violation in violations))
