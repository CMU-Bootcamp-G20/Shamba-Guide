from __future__ import annotations

from pathlib import Path
from fastapi.testclient import TestClient

from shambaguide.api import create_app
from shambaguide.config import Settings
from shambaguide.safety import RAIN_SPRAY_RULE_ID

from conftest import (
    InspectPlanner,
    SprayThenInspectPlanner,
    StaticRetriever,
    UnsafeRepairPlanner,
)

def _settings(db_path: Path) -> Settings:
    return Settings(
        sqlite_path=db_path,
        cors_origins=("http://localhost:5173",),
        max_repair_attempts=1,
    )

def test_liveness_and_readiness(tmp_path: Path) -> None:
    app = create_app(settings=_settings(tmp_path / "api.sqlite3"))
    with TestClient(app) as client:
        live = client.get("/health/live")
        ready = client.get("/health/ready")

    assert live.status_code == 200
    assert live.json()["status"] == "ok"
    assert ready.status_code == 200
    assert ready.json()["database"] == "ready"
    assert ready.json()["advice_mode"] == "safe-abstention"

def test_no_evidence_abstains_and_persists_receipt(
    tmp_path: Path,
    request_payload: dict[str, object],
) -> None:
    app = create_app(settings=_settings(tmp_path / "api.sqlite3"))
    with TestClient(app) as client:
        response = client.post("/api/v1/advice", json=request_payload)
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "abstained"
        assert payload["actions"] == []
        assert payload["sources"] == []

        receipt = client.get(f"/api/v1/receipts/{payload['receipt_id']}")

    assert receipt.status_code == 200
    receipt_payload = receipt.json()
    assert receipt_payload["request"]["session_id"] == "demo-001"
    assert receipt_payload["response"]["receipt_id"] == payload["receipt_id"]

def test_reviewed_evidence_and_safe_plan_are_approved(
    tmp_path: Path,
    request_payload: dict[str, object],
    evidence,
) -> None:
    app = create_app(
        settings=_settings(tmp_path / "api.sqlite3"),
        retriever=StaticRetriever(evidence),
        planner=InspectPlanner(),
    )
    with TestClient(app) as client:
        response = client.post("/api/v1/advice", json=request_payload)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "approved"
    assert payload["actions"][0]["category"] == "inspect"
    assert payload["sources"][0]["source_id"] == "rab-maize-001-p12"
    assert payload["model_version"] == "test-planner-inspect"

def test_high_rain_triggers_one_safe_repair(
    tmp_path: Path,
    request_payload: dict[str, object],
    evidence,
    rainy_weather,
) -> None:
    app = create_app(
        settings=_settings(tmp_path / "api.sqlite3"),
        retriever=StaticRetriever(evidence),
        planner=SprayThenInspectPlanner(),
    )
    with TestClient(app) as client:
        app.state.store.upsert_weather(rainy_weather)
        response = client.post("/api/v1/advice", json=request_payload)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "repaired"
    assert payload["actions"][0]["category"] == "inspect"
    assert RAIN_SPRAY_RULE_ID in payload["applied_rule_ids"]
    assert payload["weather_record_id"] == rainy_weather.record_id

def test_second_unsafe_plan_is_blocked(
    tmp_path: Path,
    request_payload: dict[str, object],
    evidence,
    rainy_weather,
) -> None:
    app = create_app(
        settings=_settings(tmp_path / "api.sqlite3"),
        retriever=StaticRetriever(evidence),
        planner=UnsafeRepairPlanner(),
    )
    with TestClient(app) as client:
        app.state.store.upsert_weather(rainy_weather)
        response = client.post("/api/v1/advice", json=request_payload)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "blocked"
    assert payload["actions"] == []
    assert RAIN_SPRAY_RULE_ID in payload["applied_rule_ids"]

def test_unknown_request_fields_are_rejected(
    tmp_path: Path,
    request_payload: dict[str, object],
) -> None:
    app = create_app(settings=_settings(tmp_path / "api.sqlite3"))
    request_payload["unexpected"] = "not allowed"
    with TestClient(app) as client:
        response = client.post("/api/v1/advice", json=request_payload)

    assert response.status_code == 422
