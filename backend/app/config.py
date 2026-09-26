"""SonoScribe — Centralized configuration from environment variables."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment / .env file."""

    # ── Database ──
    database_url: str = "sqlite+aiosqlite:///./sonoscribe.db"

    # ── Audio ──
    audio_sample_rate: int = 16000
    store_raw_audio: bool = False
    audio_storage_dir: str = "./audio_storage"

    # ── Transcription ──
    transcription_provider: str = "faster-whisper"
    faster_whisper_model: str = "base.en"
    faster_whisper_compute_type: str = "int8"
    faster_whisper_device: str = "cpu"

    # ── Hugging Face ──
    huggingface_api_key: str = ""
    huggingface_model: str = "meta-llama/Llama-3.1-3B-Instruct"

    # ── Groq ──
    groq_api_key: str = ""
    groq_transcription_model: str = "whisper-large-v3"

    # ── AI Notes ──
    ai_provider: str = "huggingface"
    groq_ai_model: str = "llama-3.3-70b-versatile"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # ── Server ──
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    log_level: str = "info"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return [s.strip() for s in v.split(",") if s.strip()]
        return v

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


# Singleton instance
settings = Settings()
