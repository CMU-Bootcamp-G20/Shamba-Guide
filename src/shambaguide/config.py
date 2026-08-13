from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

def _as_bool(value: str | None, *, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}

def _as_csv(value: str | None, *, default: tuple[str, ...] = ()) -> tuple[str, ...]:
    if value is None:
        return default
    return tuple(item.strip() for item in value.split(",") if item.strip())

@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str = "ShambaGuide API"
    app_env: str = "development"
    api_prefix: str = "/api/v1"
    sqlite_path: Path = Path("runtime/db/shambaguide.sqlite3")
    cors_origins: tuple[str, ...] = ("http://localhost:5173",)
    max_repair_attempts: int = 1
    docs_enabled: bool = True

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            app_name=os.getenv("APP_NAME", "ShambaGuide API"),
            app_env=os.getenv("APP_ENV", "development"),
            api_prefix=os.getenv("API_PREFIX", "/api/v1"),
            sqlite_path=Path(
                os.getenv("SQLITE_PATH", "runtime/db/shambaguide.sqlite3")
            ),
            cors_origins=_as_csv(
                os.getenv("CORS_ORIGINS"),
                default=("http://localhost:5173",),
            ),
            max_repair_attempts=max(
                0,
                int(os.getenv("MAX_REPAIR_ATTEMPTS", "1")),
            ),
            docs_enabled=_as_bool(os.getenv("DOCS_ENABLED"), default=True),
        )
