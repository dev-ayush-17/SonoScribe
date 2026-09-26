"""Pydantic schemas for API request/response validation."""

from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field


# ── Meeting Schemas ──

class MeetingCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    audio_device: Optional[str] = None


class MeetingUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    status: Optional[str] = None


class MeetingResponse(BaseModel):
    id: str
    title: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    status: str
    audio_device: Optional[str] = None
    sample_rate: int
    segment_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MeetingDetail(MeetingResponse):
    segments: List[TranscriptSegmentResponse] = []
    ai_notes: List[AiNoteResponse] = []


# ── Transcript Segment Schemas ──

class TranscriptSegmentResponse(BaseModel):
    id: str
    meeting_id: str
    segment_index: int
    start_time: float
    end_time: float
    text: str
    confidence: Optional[float] = None
    provider: str
    model: Optional[str] = None
    status: str
    language: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── AI Notes Schemas ──

class AiNoteRequest(BaseModel):
    provider: Optional[str] = None  # Override config default
    model: Optional[str] = None


class ActionItem(BaseModel):
    task: str
    owner: str = "unspecified"
    due_date: str = "unspecified"


class AiNoteResponse(BaseModel):
    id: str
    meeting_id: str
    provider: str
    model: Optional[str] = None
    summary: Optional[str] = None
    decisions: Optional[List[str]] = None
    action_items: Optional[List[ActionItem]] = None
    open_questions: Optional[List[str]] = None
    notable_timestamps: Optional[List[str]] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Recording Schemas ──

class RecordingStartRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    audio_device: Optional[str] = None
    include_microphone: bool = False


class RecordingStartResponse(BaseModel):
    meeting_id: str
    status: str
    message: str


class RecordingStopResponse(BaseModel):
    meeting_id: str
    status: str
    duration_seconds: float
    segment_count: int
    message: str


class RecordingStatusResponse(BaseModel):
    is_recording: bool
    meeting_id: Optional[str] = None
    status: str  # idle|recording|transcribing|paused|error
    duration_seconds: float = 0.0
    segment_count: int = 0
    error: Optional[str] = None


# ── Audio Device Schemas ──

class AudioDeviceInfo(BaseModel):
    index: int
    name: str
    max_input_channels: int
    max_output_channels: int
    default_sample_rate: float
    is_loopback: bool = False


# ── Health / Config Schemas ──

class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
    platform: str
    transcription_provider: str
    transcription_available: bool
    ai_provider: str
    ai_available: bool
    database: str = "connected"


class ProviderStatus(BaseModel):
    name: str
    type: str  # transcription | ai
    available: bool
    configured: bool
    error: Optional[str] = None


class ConfigResponse(BaseModel):
    transcription: ProviderStatus
    ai: ProviderStatus
    audio_sample_rate: int
    store_raw_audio: bool


# ── Export Schemas ──

class ExportRequest(BaseModel):
    format: str = Field("markdown", pattern="^(markdown|text|json)$")


# Forward reference resolution
MeetingDetail.model_rebuild()
