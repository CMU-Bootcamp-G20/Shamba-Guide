from __future__ import annotations

import uuid
from collections.abc import Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware

from shambaguide import __version__
from shambaguide.config import Settings
from shambaguide.db import SQLiteStore
from shambaguide.model import DisabledPlanner, Planner
from shambaguide.rag import EmptyRetriever, Retriever
from shambaguide.safety import SafetyEngine
from shambaguide.schemas import (
    AdviceRequest,
    AdviceResponse,
    DecisionReceipt,
    HealthResponse,
    ReadinessResponse,
)
from shambaguide.service import AdviceService

def create_app(
    *,
    settings: Settings | None = None,
    retriever: Retriever | None = None,
    planner: Planner | None = None,
) -> FastAPI:
    config = settings or Settings.from_env()
    configured_retriever = retriever or EmptyRetriever()
    configured_planner = planner or DisabledPlanner()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        store = SQLiteStore(config.sqlite_path)
        store.initialize()
        app.state.store = store
        app.state.advice_service = AdviceService(
            store=store,
            retriever=configured_retriever,
            planner=configured_planner,
            safety=SafetyEngine(),
            max_repair_attempts=config.max_repair_attempts,
        )
        yield

    app = FastAPI(
        title=config.app_name,
        version=__version__,
        description=(
            "Offline, traceable agricultural advisory API. The default development "
            "mode abstains until reviewed retrieval and a local planner are connected."
        ),
        lifespan=lifespan,
        docs_url="/docs" if config.docs_enabled else None,
        redoc_url="/redoc" if config.docs_enabled else None,
        openapi_url="/openapi.json" if config.docs_enabled else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(config.cors_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-Request-ID"],
    )

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next: Callable):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    @app.get(
        "/health/live",
        response_model=HealthResponse,
        tags=["health"],
        summary="Liveness check",
    )
    def live() -> HealthResponse:
        return HealthResponse(status="ok", version=__version__)

    @app.get(
        "/health/ready",
        response_model=ReadinessResponse,
        tags=["health"],
        summary="Readiness and component status",
    )
    def ready(request: Request) -> ReadinessResponse:
        service = _service(request)
        database_status = "ready" if service.store.ping() else "unavailable"
        planner_status = service.planner.model_version
        retriever_status = service.retriever.name
        configured = (
            planner_status != "not-configured"
            and retriever_status != "not-configured"
        )
        return ReadinessResponse(
            status=(
                "ready"
                if database_status == "ready" and configured
                else "degraded"
            ),
            database=database_status,
            retriever=retriever_status,
            planner=planner_status,
            advice_mode="full" if configured else "safe-abstention",
        )

    @app.post(
        f"{config.api_prefix}/advice",
        response_model=AdviceResponse,
        status_code=status.HTTP_200_OK,
        tags=["advice"],
        summary="Build one traceable advisory response",
    )
    def advice(payload: AdviceRequest, request: Request) -> AdviceResponse:
        return _service(request).build_advice(payload)

    @app.get(
        f"{config.api_prefix}/receipts/{{receipt_id}}",
        response_model=DecisionReceipt,
        tags=["receipts"],
        summary="Retrieve one decision receipt",
    )
    def receipt(receipt_id: str, request: Request) -> DecisionReceipt:
        record = _service(request).get_receipt(receipt_id)
        if record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Decision receipt not found.",
            )
        return record

    # Small compatibility aliases for the original starter client.
    @app.get("/health", include_in_schema=False)
    def legacy_health() -> HealthResponse:
        return live()

    @app.post("/advice", response_model=AdviceResponse, include_in_schema=False)
    def legacy_advice(payload: AdviceRequest, request: Request) -> AdviceResponse:
        return advice(payload, request)

    return app

def _service(request: Request) -> AdviceService:
    service = getattr(request.app.state, "advice_service", None)
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Application services are not initialized.",
        )
    return service

app = create_app()
