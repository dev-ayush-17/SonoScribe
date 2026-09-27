import io
import logging
import wave
from datetime import datetime, timezone
from typing import Optional

import numpy as np
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import Meeting, TranscriptSegment
from app.schemas import (
    AudioDeviceInfo,
    RecordingStartRequest,
    RecordingStartResponse,
    RecordingStatusResponse,
    RecordingStopResponse,
)
from app.services.audio.capture import AudioCaptureService
from app.services.recording import recording_manager
from app.services.session_files import session_file_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recording", tags=["recording"])


def _decode_audio_file(file_bytes: bytes) -> tuple[np.ndarray, int]:
    """Decode WAV file bytes into float32 numpy array and sample rate."""
    try:
        with wave.open(io.BytesIO(file_bytes), "rb") as wf:
            sample_rate = wf.getframerate()
            n_channels = wf.getnchannels()
            n_frames = wf.getnframes()
            frames = wf.readframes(n_frames)
            audio_int16 = np.frombuffer(frames, dtype=np.int16)
            if n_channels > 1:
                audio_int16 = audio_int16.reshape(-1, n_channels).mean(axis=1)
            audio_float32 = audio_int16.astype(np.float32) / 32768.0
            return audio_float32, sample_rate
    except Exception as wav_err:
        raise ValueError(f"Unsupported audio format (must be 16-bit WAV): {wav_err}")


@router.get("/status", response_model=RecordingStatusResponse)
async def get_recording_status() -> RecordingStatusResponse:
    """Get current recording status."""
    status = recording_manager.get_status()
    return RecordingStatusResponse(**status)


@router.get("/devices")
async def list_audio_devices() -> list:
    """List available audio capture devices."""
    devices = AudioCaptureService.list_devices()
    return [
        {
            "index": d.index,
            "name": d.name,
            "max_input_channels": d.max_input_channels,
            "max_output_channels": d.max_output_channels,
            "default_sample_rate": d.default_sample_rate,
            "is_loopback": d.is_loopback,
            "hostapi_name": d.hostapi_name,
        }
        for d in devices
    ]


@router.post("/start", response_model=RecordingStartResponse)
async def start_recording(
    request: RecordingStartRequest,
    db: AsyncSession = Depends(get_db),
) -> RecordingStartResponse:
    """Start recording a new meeting."""
    if recording_manager.is_recording:
        raise HTTPException(
            status_code=409,
            detail=f"Already recording meeting {recording_manager.active_meeting_id}",
        )

    # Create meeting record
    meeting = Meeting(
        title=request.title,
        started_at=datetime.now(timezone.utc),
        status="recording",
        audio_device=request.audio_device,
    )
    db.add(meeting)
    await db.flush()  # Get the ID
    meeting_id = meeting.id

    try:
        # Parse device index if provided
        device_index = None
        if request.audio_device:
            try:
                device_index = int(request.audio_device)
            except ValueError:
                # Try to find by name
                devices = AudioCaptureService.list_devices()
                for d in devices:
                    if request.audio_device.lower() in d.name.lower():
                        device_index = d.index
                        break

        device_name = await recording_manager.start_recording(
            meeting_id=meeting_id,
            device_index=device_index,
        )

        # Update meeting with actual device info
        meeting.audio_device = device_name
        await db.flush()

        logger.info("Recording started: meeting=%s device=%s", meeting_id, device_name)

        return RecordingStartResponse(
            meeting_id=meeting_id,
            status="recording",
            message=f"Recording started on {device_name}",
        )

    except Exception as e:
        # Mark meeting as failed
        meeting.status = "failed"
        await db.flush()
        logger.error("Failed to start recording: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop", response_model=RecordingStopResponse)
async def stop_recording(
    db: AsyncSession = Depends(get_db),
) -> RecordingStopResponse:
    """Stop the active recording."""
    if not recording_manager.is_recording:
        raise HTTPException(status_code=404, detail="No active recording")

    meeting_id = recording_manager.active_meeting_id

    try:
        result = await recording_manager.stop_recording()

        return RecordingStopResponse(
            meeting_id=result["meeting_id"],
            status="completed",
            duration_seconds=result["duration_seconds"],
            segment_count=result["segment_count"],
            message=f"Recording stopped. {result['segment_count']} segments saved.",
        )

    except Exception as e:
        logger.error("Failed to stop recording: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_audio_recording(
    file: UploadFile = File(...),
    title: Optional[str] = Form("Tab Capture Session"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Upload audio file (from Chrome Extension) and process transcription & AI notes."""
    if not file:
        raise HTTPException(status_code=400, detail="No audio file provided")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file")

    # Create meeting record in DB
    meeting = Meeting(
        title=title or "Tab Capture Session",
        started_at=datetime.now(timezone.utc),
        status="completed",
        audio_device="Chrome Extension TabCapture",
    )
    db.add(meeting)
    await db.flush()
    meeting_id = meeting.id

    try:
        audio_data, sample_rate = _decode_audio_file(file_bytes)
    except Exception as e:
        logger.error("Failed to decode uploaded audio file: %s", e)
        raise HTTPException(status_code=400, detail=f"Failed to decode audio file: {e}")

    duration_seconds = len(audio_data) / float(sample_rate) if sample_rate else 0.0
    meeting.duration_seconds = duration_seconds
    meeting.ended_at = datetime.now(timezone.utc)

    if settings.store_raw_audio:
        raw_path = session_file_manager.save_raw_audio(meeting_id, file_bytes, extension="wav")
        meeting.raw_audio_path = raw_path

    provider = recording_manager._get_provider()
    chunk_samples = sample_rate * 60
    chunks = [audio_data[i:i + chunk_samples] for i in range(0, len(audio_data), chunk_samples)] or [audio_data]

    segment_index = 0
    full_transcript_lines = []

    for idx, chunk in enumerate(chunks):
        chunk_start_time = idx * 60.0
        results = await provider.transcribe(chunk, sample_rate=sample_rate)
        for r in results:
            seg = TranscriptSegment(
                meeting_id=meeting_id,
                segment_index=segment_index,
                start_time=chunk_start_time + r.start_time,
                end_time=chunk_start_time + r.end_time,
                text=r.text,
                confidence=r.confidence,
                provider=r.provider,
                model=r.model,
                status="final",
                language=r.language,
            )
            db.add(seg)
            segment_index += 1
            full_transcript_lines.append(f"[{chunk_start_time + r.start_time:.1f}s] {r.text}")

    await db.commit()

    raw_transcript_text = "\n".join(full_transcript_lines)
    session_file_manager.write_raw_transcript(meeting_id, raw_transcript_text)


    artifacts = {}
    try:
        from app.services.ai.notes import generate_windowed_meeting_artifacts
        artifacts = await generate_windowed_meeting_artifacts(meeting_id, raw_transcript_text)
    except Exception as e:
        logger.warning("AI notes generation for uploaded session failed: %s", e)

    return {
        "status": "completed",
        "meeting_id": meeting_id,
        "title": meeting.title,
        "duration_seconds": duration_seconds,
        "segment_count": segment_index,
        "artifacts": artifacts,
    }

