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
        """
        Builds an advisory response using an Extractive RAG approach.
        """
        evidence = self.retriever.retrieve(request, top_k=5)
        weather = self.store.get_current_weather(
            district=request.district,
            sector=request.sector,
        )

        # 1. Handle Empty Results (No matches in the database)
        if not evidence:
            return self._finalize(
                request,
                AdviceResponse(
                    receipt_id=_new_receipt_id(),
                    status=AdviceStatus.ABSTAINED,
                    message=(
                        "Ntabwo nabashije kubona amakuru yemejwe na RAB kuri iki kibazo. "
                        "Ushobora kubaza umujyanama w'ubuhinzi."
                    ),
                    actions=[],
                    warnings=["No reviewed local evidence is available."],
                    sources=[],
                    applied_rule_ids=[],
                    weather_record_id=weather.record_id if weather else None,
                    model_version="extractive-rag",
                ),
            )

        # 2. Hardcoded Deterministic Safety Rules
        danger_keywords = ["ddt", "endosulfan", "malariya", "malaria"]
        query_lower = request.question.lower()
        
        if any(word in query_lower for word in danger_keywords):
            return self._finalize(
                request,
                AdviceResponse(
                    receipt_id=_new_receipt_id(),
                    status=AdviceStatus.BLOCKED,
                    message="Kuvura indwara z'abantu cyangwa gukoresha imiti yashyizweho imbago nka DDT ntabwo byemewe.",
                    actions=[],
                    warnings=["Query blocked due to safety violations (banned chemicals or medical)."],
                    sources=_source_references(evidence),
                    applied_rule_ids=["rule-banned-substance-01"],
                    weather_record_id=weather.record_id if weather else None,
                    model_version="extractive-rag-safety",
                ),
            )

        # 3. Extractive RAG: Map the top retrieved text directly to the UI
        best_evidence = evidence[0]

        return self._finalize(
            request,
            AdviceResponse(
                receipt_id=_new_receipt_id(),
                status=AdviceStatus.APPROVED,
                message="Dore amakuru yemejwe na RAB twagushakiye:",
                actions=[
                    AdviceAction(
                        action_id=f"act-{uuid.uuid4().hex[:8]}",
                        category="inspect",
                        text=best_evidence.text,
                        timeframe="Uyu munsi",
                        reason="Amabwiriza ya RAB",
                        source_ids=[best_evidence.source_id],
                    )
                ],
                warnings=[],
                sources=_source_references(evidence),
                applied_rule_ids=["rule-extractive-01"],
                weather_record_id=weather.record_id if weather else None,
                model_version="extractive-rag",
            ),
        )

    def get_receipt(self, receipt_id: str) -> DecisionReceipt | None:
        return self.store.get_receipt(receipt_id)

    def _finalize(
        self,
        request: AdviceRequest,
        response: AdviceResponse,
    ) -> AdviceResponse:
        """Saves the interaction to the SQLite database and returns the response."""
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