from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Language(StrEnum):
    ENGLISH = "en"
    KINYARWANDA = "rw"


class Channel(StrEnum):
    WEB = "web"
    USSD = "ussd"
    API = "api"


class AdviceStatus(StrEnum):
    APPROVED = "approved"
    REPAIRED = "repaired"
    BLOCKED = "blocked"
    ABSTAINED = "abstained"

class ActionCategory(StrEnum):
    INSPECT = "inspect"
    SPRAY = "spray"
    IRRIGATE = "irrigate"
    FERTILIZE = "fertilize"
    PLANT = "plant"
    HARVEST = "harvest"
    ESCALATE = "escalate"
    OTHER = "other"

class AdviceRequest(StrictModel):
    session_id: str = Field(min_length=1, max_length=100)
    question: str = Field(min_length=3, max_length=1000)
    crop: str = Field(min_length=2, max_length=100)
    district: str = Field(min_length=2, max_length=100)
    sector: str | None = Field(default=None, max_length=100)
    growth_stage: str | None = Field(default=None, max_length=100)
    language: Language = Language.ENGLISH
    channel: Channel = Channel.API

class EvidenceChunk(StrictModel):
    source_id: str = Field(min_length=1, max_length=200)
    title: str = Field(min_length=1, max_length=300)
    text: str = Field(min_length=1, max_length=20_000)
    page: int | None = Field(default=None, ge=1)
    section: str | None = Field(default=None, max_length=300)
    score: float = 0.0

class WeatherSnapshot(StrictModel):
    record_id: str = Field(min_length=1, max_length=200)
    district: str = Field(min_length=2, max_length=100)
    sector: str | None = Field(default=None, max_length=100)
    issued_at: datetime
    valid_from: datetime
    valid_to: datetime
    rain_probability_6h: float | None = Field(default=None, ge=0.0, le=1.0)
    temperature_c: float | None = Field(default=None, ge=-20.0, le=60.0)
    relative_humidity_pct: float | None = Field(default=None, ge=0.0, le=100.0)

    @model_validator(mode="after")
    def validate_window(self) -> WeatherSnapshot:
        for field_name in ("issued_at", "valid_from", "valid_to"):
            value = getattr(self, field_name)
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError(f"{field_name} must include a timezone")
            setattr(self, field_name, value.astimezone(UTC))
        if self.valid_from > self.valid_to:
            raise ValueError("valid_from must be before valid_to")
        return self

class DraftAction(StrictModel):
    action_id: str = Field(min_length=1, max_length=100)
    category: ActionCategory
    instruction: str = Field(min_length=3, max_length=500)
    timeframe: str | None = Field(default=None, max_length=100)
    reason: str | None = Field(default=None, max_length=500)
    source_ids: list[str] = Field(default_factory=list, max_length=10)

class DraftActionPlan(StrictModel):
    summary: str = Field(min_length=3, max_length=1000)
    actions: list[DraftAction] = Field(default_factory=list, max_length=10)
    warnings: list[str] = Field(default_factory=list, max_length=10)
    requires_extension_officer: bool = False

class SafetyViolation(StrictModel):
    rule_id: str
    message: str
    action_id: str | None = None

class SourceReference(StrictModel):
    source_id: str
    title: str
    page: int | None = None
    section: str | None = None

class AdviceAction(StrictModel):
    action_id: str
    category: ActionCategory
    text: str
    timeframe: str | None = None
    reason: str | None = None
    source_ids: list[str] = Field(default_factory=list)

class AdviceResponse(StrictModel):
    receipt_id: str
    status: AdviceStatus
    message: str
    actions: list[AdviceAction] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    sources: list[SourceReference] = Field(default_factory=list)
    applied_rule_ids: list[str] = Field(default_factory=list)
    weather_record_id: str | None = None
    model_version: str = "not-configured"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

class DecisionReceipt(StrictModel):
    receipt_id: str
    request: AdviceRequest
    response: AdviceResponse
    created_at: datetime

class HealthResponse(StrictModel):
    status: str
    version: str

class ReadinessResponse(StrictModel):
    status: str
    database: str
    retriever: str
    planner: str
    advice_mode: str
