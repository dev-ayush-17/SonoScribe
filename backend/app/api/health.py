"""Health check and configuration endpoints."""

from __future__ import annotations

import platform

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.config import settings
from app.database import get_db
from app.schemas import HealthResponse, ConfigResponse, ProviderStatus

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    """Check application health and provider availability."""
    # Check database
    db_status = "connected"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    # Check transcription provider
    transcription_available = False
    if settings.transcription_provider == "faster-whisper":
        try:
            import faster_whisper  # noqa: F401
            transcription_available = True
        except ImportError:
            pass
    elif settings.transcription_provider == "groq":
        transcription_available = bool(settings.groq_api_key)

    # Check AI provider
    ai_available = False
    if settings.ai_provider == "groq":
        ai_available = bool(settings.groq_api_key)
    elif settings.ai_provider == "ollama":
        ai_available = True  # Assume available if configured
    elif settings.ai_provider == "gemini":
        ai_available = bool(settings.gemini_api_key)

    return HealthResponse(
        status="ok" if db_status == "connected" else "degraded",
        platform=platform.system(),
        transcription_provider=settings.transcription_provider,
        transcription_available=transcription_available,
        ai_provider=settings.ai_provider,
        ai_available=ai_available,
        database=db_status,
    )


@router.get("/config", response_model=ConfigResponse)
async def get_config() -> ConfigResponse:
    """Get current provider configuration."""
    # Transcription status
    transcription_error = None
    transcription_available = False
    if settings.transcription_provider == "faster-whisper":
        try:
            import faster_whisper  # noqa: F401
            transcription_available = True
        except ImportError:
            transcription_error = "faster-whisper not installed. Run: pip install faster-whisper"
    elif settings.transcription_provider == "groq":
        if settings.groq_api_key:
            transcription_available = True
        else:
            transcription_error = "GROQ_API_KEY not set"

    # AI status
    ai_error = None
    ai_available = False
    ai_configured = settings.ai_provider != "none"
    if settings.ai_provider == "groq":
        if settings.groq_api_key:
            ai_available = True
        else:
            ai_error = "GROQ_API_KEY not set"
    elif settings.ai_provider == "ollama":
        ai_available = True
    elif settings.ai_provider == "gemini":
        if settings.gemini_api_key:
            ai_available = True
        else:
            ai_error = "GEMINI_API_KEY not set"

    return ConfigResponse(
        transcription=ProviderStatus(
            name=settings.transcription_provider,
            type="transcription",
            available=transcription_available,
            configured=True,
            error=transcription_error,
        ),
        ai=ProviderStatus(
            name=settings.ai_provider,
            type="ai",
            available=ai_available,
            configured=ai_configured,
            error=ai_error,
        ),
        audio_sample_rate=settings.audio_sample_rate,
        store_raw_audio=settings.store_raw_audio,
    )
