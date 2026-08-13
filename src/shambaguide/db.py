from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from shambaguide.schemas import (
    AdviceRequest,
    AdviceResponse,
    DecisionReceipt,
    WeatherSnapshot,
)

class SQLiteStore:
    """Small SQLite persistence layer for weather data and decision receipts."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=5.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        return connection

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS decision_receipts (
                    receipt_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    request_json TEXT NOT NULL,
                    response_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_receipts_session_created
                    ON decision_receipts(session_id, created_at DESC);

                CREATE TABLE IF NOT EXISTS weather_cache (
                    record_id TEXT PRIMARY KEY,
                    district TEXT NOT NULL,
                    district_key TEXT NOT NULL,
                    sector TEXT,
                    sector_key TEXT,
                    issued_at TEXT NOT NULL,
                    valid_from TEXT NOT NULL,
                    valid_to TEXT NOT NULL,
                    rain_probability_6h REAL,
                    temperature_c REAL,
                    relative_humidity_pct REAL
                );

                CREATE INDEX IF NOT EXISTS idx_weather_location_validity
                    ON weather_cache(district_key, sector_key, valid_from, valid_to);
                """
            )

    def ping(self) -> bool:
        try:
            with self._connect() as connection:
                row = connection.execute("SELECT 1 AS ok").fetchone()
            return bool(row and row["ok"] == 1)
        except sqlite3.Error:
            return False

    def save_receipt(
        self,
        request: AdviceRequest,
        response: AdviceResponse,
    ) -> DecisionReceipt:
        created_at = response.created_at
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO decision_receipts (
                    receipt_id,
                    session_id,
                    status,
                    request_json,
                    response_json,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    response.receipt_id,
                    request.session_id,
                    response.status.value,
                    request.model_dump_json(),
                    response.model_dump_json(),
                    created_at.isoformat(),
                ),
            )
        return DecisionReceipt(
            receipt_id=response.receipt_id,
            request=request,
            response=response,
            created_at=created_at,
        )

    def get_receipt(self, receipt_id: str) -> DecisionReceipt | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT receipt_id, request_json, response_json, created_at
                FROM decision_receipts
                WHERE receipt_id = ?
                """,
                (receipt_id,),
            ).fetchone()

        if row is None:
            return None

        return DecisionReceipt(
            receipt_id=row["receipt_id"],
            request=AdviceRequest.model_validate_json(row["request_json"]),
            response=AdviceResponse.model_validate_json(row["response_json"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def upsert_weather(self, weather: WeatherSnapshot) -> None:
        district_key = _normalise_location(weather.district)
        sector_key = _normalise_location(weather.sector) if weather.sector else None
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO weather_cache (
                    record_id,
                    district,
                    district_key,
                    sector,
                    sector_key,
                    issued_at,
                    valid_from,
                    valid_to,
                    rain_probability_6h,
                    temperature_c,
                    relative_humidity_pct
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(record_id) DO UPDATE SET
                    district = excluded.district,
                    district_key = excluded.district_key,
                    sector = excluded.sector,
                    sector_key = excluded.sector_key,
                    issued_at = excluded.issued_at,
                    valid_from = excluded.valid_from,
                    valid_to = excluded.valid_to,
                    rain_probability_6h = excluded.rain_probability_6h,
                    temperature_c = excluded.temperature_c,
                    relative_humidity_pct = excluded.relative_humidity_pct
                """,
                (
                    weather.record_id,
                    weather.district,
                    district_key,
                    weather.sector,
                    sector_key,
                    weather.issued_at.isoformat(),
                    weather.valid_from.isoformat(),
                    weather.valid_to.isoformat(),
                    weather.rain_probability_6h,
                    weather.temperature_c,
                    weather.relative_humidity_pct,
                ),
            )

    def get_current_weather(
        self,
        *,
        district: str,
        sector: str | None,
        at: datetime | None = None,
    ) -> WeatherSnapshot | None:
        current_time = (at or datetime.now(UTC)).isoformat()
        district_key = _normalise_location(district)
        sector_key = _normalise_location(sector) if sector else None

        if sector_key is None:
            query = """
                SELECT *
                FROM weather_cache
                WHERE district_key = ?
                  AND sector_key IS NULL
                  AND valid_from <= ?
                  AND valid_to >= ?
                ORDER BY issued_at DESC
                LIMIT 1
            """
            params = (district_key, current_time, current_time)
        else:
            query = """
                SELECT *
                FROM weather_cache
                WHERE district_key = ?
                  AND (sector_key = ? OR sector_key IS NULL)
                  AND valid_from <= ?
                  AND valid_to >= ?
                ORDER BY
                    CASE WHEN sector_key = ? THEN 0 ELSE 1 END,
                    issued_at DESC
                LIMIT 1
            """
            params = (
                district_key,
                sector_key,
                current_time,
                current_time,
                sector_key,
            )

        with self._connect() as connection:
            row = connection.execute(query, params).fetchone()

        if row is None:
            return None

        return WeatherSnapshot(
            record_id=row["record_id"],
            district=row["district"],
            sector=row["sector"],
            issued_at=datetime.fromisoformat(row["issued_at"]),
            valid_from=datetime.fromisoformat(row["valid_from"]),
            valid_to=datetime.fromisoformat(row["valid_to"]),
            rain_probability_6h=row["rain_probability_6h"],
            temperature_c=row["temperature_c"],
            relative_humidity_pct=row["relative_humidity_pct"],
        )

    def export_receipt_json(self, receipt_id: str) -> str | None:
        receipt = self.get_receipt(receipt_id)
        if receipt is None:
            return None
        return json.dumps(receipt.model_dump(mode="json"), indent=2, sort_keys=True)

    def get_all_sessions(self) -> list[dict]:
        """Groups receipts to return a list of unique chat sessions."""
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT 
                    session_id, 
                    MAX(created_at) as updated_at, 
                    COUNT(receipt_id) as message_count
                FROM decision_receipts
                GROUP BY session_id
                ORDER BY updated_at DESC
                LIMIT 50
                """
            ).fetchall()
            
        return [
            {
                "conversation_id": row["session_id"],
                "message_count": row["message_count"],
                "updated_at": row["updated_at"]
            }
            for row in rows
        ]

    def get_session_history(self, session_id: str) -> list[dict]:
        """Retrieves all interactions for a specific session in chronological order."""
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT request_json, response_json, created_at
                FROM decision_receipts
                WHERE session_id = ?
                ORDER BY created_at ASC
                """,
                (session_id,)
            ).fetchall()

        history = []
        for row in rows:
            req = json.loads(row["request_json"])
            res = json.loads(row["response_json"])
            # Format to match frontend expectations roughly
            history.append({
                "role": "user",
                "content": req.get("question", ""),
                "created_at": row["created_at"]
            })
            history.append({
                "role": "assistant",
                "content": res.get("message", ""),
                "actions": res.get("actions", []),
                "status": res.get("status", ""),
                "created_at": row["created_at"]
            })
        return history

    def get_basic_analytics(self) -> dict:
        """Returns simple counts for the dashboard."""
        with self._connect() as connection:
            total_questions = connection.execute("SELECT COUNT(*) FROM decision_receipts").fetchone()[0]
            total_sessions = connection.execute("SELECT COUNT(DISTINCT session_id) FROM decision_receipts").fetchone()[0]
            
        return {
            "summary": {
                "total_questions": total_questions,
                "total_conversations": total_sessions
            }
        }
def _normalise_location(value: str) -> str:
    return " ".join(value.casefold().split())
