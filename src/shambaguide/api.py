from __future__ import annotations

import io
import uuid
from collections.abc import Callable
from contextlib import asynccontextmanager

import scipy.io.wavfile as wavfile
import torch
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from huggingface_hub import hf_hub_download
from pydantic import BaseModel

from deepkin.data.kinya_norm import text_to_sequence
from deepkin.models.flex_tts import FlexKinyaTTS
from deepkin.modules.tts_commons import intersperse

from shambaguide import __version__
from shambaguide.config import Settings
from shambaguide.db import SQLiteStore
from shambaguide.model import DisabledPlanner, Planner
from shambaguide.rag import KinyaColBERTRetriever, Retriever
from shambaguide.safety import SafetyEngine
from shambaguide.schemas import (
    AdviceRequest,
    AdviceResponse,
    DecisionReceipt,
    HealthResponse,
    ReadinessResponse,
)
from shambaguide.service import AdviceService


class TTSRequest(BaseModel):
    """Schema for Text-to-Speech API requests."""
    text: str
    speaker_id: int = 0  # 0: Female 1, 1: Female 2, 2: Male


def create_app(
    *,
    settings: Settings | None = None,
    retriever: Retriever | None = None,
    planner: Planner | None = None,
) -> FastAPI:
    """Application factory for the ShambaGuide API."""
    config = settings or Settings.from_env()
    configured_planner = planner or DisabledPlanner()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Manages the startup and shutdown lifecycle of backend dependencies."""
        # 1. Initialize SQLite Database
        store = SQLiteStore(config.sqlite_path)
        store.initialize()
        
        # 2. Initialize ColBERT Retriever
        index_path = ".ragatouille/colbert/indexes/shambaguide_kinya"
        live_retriever = retriever or KinyaColBERTRetriever(index_path=index_path, min_score=12.0)
        
        # 3. Mount core services to application state
        app.state.store = store
        app.state.advice_service = AdviceService(
            store=store,
            retriever=live_retriever,
            planner=configured_planner,
            safety=SafetyEngine(),
            max_repair_attempts=config.max_repair_attempts,
        )

        # 4. Pre-load KinyaFlexTTS model into memory once
        print("🔊 Pre-loading KinyaFlexTTS model into memory...")
        app.state.tts_model = None
        try:
            device = torch.device('cpu')
            model_path = hf_hub_download(
                repo_id="C4IR-RW/kinya-flex-tts",
                filename="kinya_flex_tts_base_trained.pt"
            )
            tts_model = FlexKinyaTTS.from_pretrained(device, model_path)
            tts_model.eval()
            app.state.tts_model = tts_model
            print("✅ KinyaFlexTTS loaded successfully!")
        except Exception as e:
            print(f"⚠️ Warning: TTS Model failed to load: {e}")

        yield
        # Resources are cleanly released here on shutdown if necessary

    # --- FastAPI Application Setup ---
    app = FastAPI(
        title=config.app_name,
        version=__version__,
        description=(
            "Offline, traceable agricultural advisory API combining "
            "Extractive RAG (KinyaColBERT) and native Voice (KinyaFlexTTS)."
        ),
        lifespan=lifespan,
        docs_url="/docs" if config.docs_enabled else None,
        redoc_url="/redoc" if config.docs_enabled else None,
        openapi_url="/openapi.json" if config.docs_enabled else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  
        allow_credentials=False,
        allow_methods=["*"],  
        allow_headers=["*"],  
    )

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next: Callable):
        """Injects a unique Request ID for end-to-end traceability."""
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    # --- HEALTH & DIAGNOSTICS ENDPOINTS ---

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

    # --- CORE ADVISORY ENDPOINTS ---

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

    # --- DASHBOARD & CHAT ENDPOINTS ---
    
    @app.get(
        f"{config.api_prefix}/chats",
        tags=["chats"],
        summary="Retrieve all chat sessions",
    )
    def list_chats(request: Request):
        return {"chats": _service(request).store.get_all_sessions()}

    @app.get(
        f"{config.api_prefix}/chats/{{session_id}}",
        tags=["chats"],
        summary="Retrieve message history for a specific session",
    )
    def get_chat_history(session_id: str, request: Request):
        history = _service(request).store.get_session_history(session_id)
        if not history:
            raise HTTPException(status_code=404, detail="Session not found")
        return {
            "conversation_id": session_id,
            "messages": history
        }

    @app.get(
        f"{config.api_prefix}/analytics",
        tags=["analytics"],
        summary="Retrieve dashboard analytics",
    )
    def get_analytics(request: Request):
        return _service(request).store.get_basic_analytics()

    # --- AUDIO (TEXT-TO-SPEECH) ENDPOINT ---

    @app.post(
        f"{config.api_prefix}/tts",
        tags=["audio"],
        summary="Generate Kinyarwanda speech from text",
    )
    def generate_speech(payload: TTSRequest, request: Request):
        """Synthesizes Kinyarwanda text into audio and returns it as a binary file."""
        tts_model = getattr(request.app.state, "tts_model", None)
        if tts_model is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
                detail="TTS service is currently unavailable."
            )

        if not payload.text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Text cannot be empty."
            )

        try:
            # 1. Process and generate audio tensor on CPU
            text_seq = intersperse(text_to_sequence(payload.text, norm=True), 0)
            with torch.no_grad():
                audio_data = tts_model(text_seq, payload.speaker_id)

            # 2. Convert PyTorch tensor to NumPy array safely
            audio_np = audio_data.squeeze().cpu().numpy()

            # 3. Save audio into in-memory bytes buffer using Scipy
            buffer = io.BytesIO()
            wavfile.write(buffer, 24000, audio_np)
            
            # 4. Return standard Response to ensure accurate Content-Length for browsers
            return Response(content=buffer.getvalue(), media_type="audio/wav")

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=f"Audio generation failed: {str(e)}"
            )

    # --- LEGACY COMPATIBILITY ALIASES ---
    
    @app.get("/health", include_in_schema=False)
    def legacy_health() -> HealthResponse:
        return live()

    @app.post("/advice", response_model=AdviceResponse, include_in_schema=False)
    def legacy_advice(payload: AdviceRequest, request: Request) -> AdviceResponse:
        return advice(payload, request)

    return app


def _service(request: Request) -> AdviceService:
    """Helper to safely retrieve the AdviceService from application state."""
    service = getattr(request.app.state, "advice_service", None)
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Application services are not initialized.",
        )
    return service

# Entry point for Uvicorn
app = create_app()