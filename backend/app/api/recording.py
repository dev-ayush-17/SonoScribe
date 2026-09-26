"""Recording control API endpoints."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Meeting
from app.schemas import (
    AudioDeviceInfo,
    RecordingStartRequest,
    RecordingStartResponse,
    RecordingStatusResponse,
    RecordingStopResponse,
)
from app.services.audio.capture import AudioCaptureService
from app.services.recording import recording_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recording", tags=["recording"])


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
