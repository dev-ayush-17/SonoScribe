"""Recording orchestrator — ties audio capture, transcription, and persistence together."""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional

import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import async_session
from app.models import Meeting, TranscriptSegment
from app.services.audio.capture import AudioCaptureService, AudioChunk
from app.services.session_files import session_file_manager
from app.services.transcription.provider import (
    TranscriptionProvider,
    TranscriptionResult,
    create_transcription_provider,
)

logger = logging.getLogger(__name__)


class RecordingSession:
    """Manages a single recording session: 1-min audio chunks → transcription → DB & session file."""

    def __init__(
        self,
        meeting_id: str,
        transcription_provider: TranscriptionProvider,
        sample_rate: int = 16000,
        on_segment: Optional[Callable] = None,
    ):
        self.meeting_id = meeting_id
        self.provider = transcription_provider
        self.sample_rate = sample_rate
        self.on_segment = on_segment

        self._audio = AudioCaptureService(
            sample_rate=sample_rate,
            chunk_duration=60.0,   # 1 minute per chunk
            overlap_duration=5.0,  # 5 seconds overlap
        )
        self._transcription_task: Optional[asyncio.Task] = None
        self._is_active = False
        self._segment_count = 0
        self._error: Optional[str] = None
        self._start_time: float = 0.0
        self._last_ai_process_time: float = 0.0
        self._failed_chunks: List[AudioChunk] = []

    @property
    def is_active(self) -> bool:
        return self._is_active

    @property
    def segment_count(self) -> int:
        return self._segment_count

    @property
    def duration_seconds(self) -> float:
        if not self._is_active:
            return 0.0
        return time.monotonic() - self._start_time

    @property
    def error(self) -> Optional[str]:
        return self._error

    @property
    def device_name(self) -> str:
        return self._audio.device_name

    async def start(self, device_index: Optional[int] = None) -> str:
        """Start recording and transcription pipeline. Returns device name."""
        if self._is_active:
            raise RuntimeError("Session already active")

        self._is_active = True
        self._start_time = time.monotonic()
        self._error = None
        self._segment_count = 0
        self._failed_chunks = []

        # Start audio capture
        device_name = await self._audio.start(device_index=device_index)

        # Start transcription worker
        self._transcription_task = asyncio.create_task(
            self._transcription_loop(),
            name=f"transcription-{self.meeting_id}",
        )

        logger.info("Recording started for meeting %s on device: %s", self.meeting_id, device_name)
        return device_name

    async def stop(self) -> dict:
        """Stop recording, flush remaining audio, return summary."""
        if not self._is_active:
            return {"segment_count": 0, "duration_seconds": 0}

        self._is_active = False
        duration = time.monotonic() - self._start_time

        # Stop audio capture (flushes remaining buffer)
        remaining_chunks = await self._audio.stop()

        # Process remaining chunks
        for chunk in remaining_chunks:
            await self._process_chunk(chunk)

        # Cancel transcription loop
        if self._transcription_task and not self._transcription_task.done():
            self._transcription_task.cancel()
            try:
                await self._transcription_task
            except asyncio.CancelledError:
                pass

        # Retry failed chunks one last time
        if self._failed_chunks:
            logger.info("Retrying %d failed chunks...", len(self._failed_chunks))
            for chunk in self._failed_chunks[:]:
                try:
                    await self._process_chunk(chunk)
                    self._failed_chunks.remove(chunk)
                except Exception as e:
                    logger.warning("Retry failed for chunk %d: %s", chunk.chunk_index, e)

        # Update meeting status
        async with async_session() as db:
            from sqlalchemy import select
            result = await db.execute(
                select(Meeting).where(Meeting.id == self.meeting_id)
            )
            meeting = result.scalar_one_or_none()
            if meeting:
                meeting.ended_at = datetime.now(timezone.utc)
                meeting.duration_seconds = duration
                meeting.status = "completed"
                await db.commit()

        logger.info(
            "Recording stopped for meeting %s: %.1fs, %d segments",
            self.meeting_id, duration, self._segment_count,
        )

        return {
            "segment_count": self._segment_count,
            "duration_seconds": duration,
            "failed_chunks": len(self._failed_chunks),
        }

    async def _transcription_loop(self):
        """Continuously poll for audio chunks and transcribe them."""
        while self._is_active:
            chunks = self._audio.get_pending_chunks()
            for chunk in chunks:
                await self._process_chunk(chunk)

            # Small sleep to avoid busy-waiting
            await asyncio.sleep(0.5)

    async def _process_chunk(self, chunk: AudioChunk):
        """Transcribe a single audio chunk and persist results."""
        try:
            # Check for silence (skip near-silent chunks)
            rms = np.sqrt(np.mean(chunk.data ** 2))
            if rms < 0.0001:  # Only skip near-total digital silence
                logger.debug("Skipping silent chunk %d (rms=%.6f)", chunk.chunk_index, rms)
                return

            logger.info(
                "Transcribing chunk %d (%.1fs-%.1fs, rms=%.4f)",
                chunk.chunk_index, chunk.start_time, chunk.end_time, rms,
            )

            results = await self.provider.transcribe(
                audio_data=chunk.data,
                sample_rate=chunk.sample_rate,
            )

            if not results:
                logger.debug("No speech in chunk %d", chunk.chunk_index)
                return

            # Combine all sub-phrases in the 1-minute chunk into a single continuous segment
            combined_text = " ".join([r.text.strip() for r in results if r.text and r.text.strip()])
            if not combined_text:
                return

            seg_start = chunk.start_time
            seg_end = chunk.end_time
            primary_provider = results[0].provider if results else "whisper"
            primary_model = results[0].model if results else "base.en"
            language = results[0].language if results else "en"

            # Persist as 1 continuous segment in DB and session text file
            async with async_session() as db:
                # Append to session's raw transcript file on disk
                session_file_manager.append_segment(
                    meeting_id=self.meeting_id,
                    start_time=seg_start,
                    end_time=seg_end,
                    text=combined_text,
                    segment_index=self._segment_count,
                )

                segment = TranscriptSegment(
                    meeting_id=self.meeting_id,
                    segment_index=self._segment_count,
                    start_time=seg_start,
                    end_time=seg_end,
                    text=combined_text,
                    confidence=results[0].confidence if hasattr(results[0], 'confidence') else 0.95,
                    provider=primary_provider,
                    model=primary_model,
                    status="final",
                    language=language,
                )
                db.add(segment)
                self._segment_count += 1

                # Notify via callback (for WebSocket live streaming)
                if self.on_segment:
                    try:
                        await self.on_segment({
                            "meeting_id": self.meeting_id,
                            "segment_index": segment.segment_index,
                            "start_time": seg_start,
                            "end_time": seg_end,
                            "text": combined_text,
                            "confidence": segment.confidence,
                        })
                    except Exception as e:
                        logger.warning("Segment callback error: %s", e)

                await db.commit()

            # Check if 20 minutes (1200s) have passed since last rolling AI processing
            elapsed_since_ai = time.monotonic() - self._last_ai_process_time
            if elapsed_since_ai >= 1200.0 and settings.ai_provider != "none":
                self._last_ai_process_time = time.monotonic()
                logger.info("20 minutes reached for meeting %s — triggering rolling AI window processing", self.meeting_id)
                asyncio.create_task(self._trigger_rolling_ai_processing())

            logger.info(
                "Chunk %d: %d segment(s) persisted",
                chunk.chunk_index, len(results),
            )

        except Exception as e:
            logger.error("Transcription failed for chunk %d: %s", chunk.chunk_index, e)
            self._error = str(e)
            self._failed_chunks.append(chunk)

    async def _trigger_rolling_ai_processing(self):
        """Run windowed AI processing in background without blocking recording."""
        try:
            from app.services.ai.notes import generate_windowed_meeting_artifacts
            raw_text = session_file_manager.read_raw_transcript(self.meeting_id)
            if raw_text:
                await generate_windowed_meeting_artifacts(self.meeting_id, raw_text)
        except Exception as e:
            logger.warning("Rolling AI background processing error: %s", e)


class RecordingManager:
    """Manages active recording sessions (singleton)."""

    def __init__(self):
        self._sessions: Dict[str, RecordingSession] = {}
        self._active_meeting_id: Optional[str] = None
        self._provider: Optional[TranscriptionProvider] = None

    def _get_provider(self) -> TranscriptionProvider:
        """Get or create the transcription provider."""
        if self._provider is None:
            self._provider = create_transcription_provider(
                provider_name=settings.transcription_provider,
                model=settings.faster_whisper_model,
                device=settings.faster_whisper_device,
                compute_type=settings.faster_whisper_compute_type,
                api_key=settings.groq_api_key,
                groq_model=settings.groq_transcription_model,
            )
        return self._provider

    @property
    def is_recording(self) -> bool:
        return self._active_meeting_id is not None

    @property
    def active_meeting_id(self) -> Optional[str]:
        return self._active_meeting_id

    def get_status(self) -> dict:
        """Get current recording status."""
        if not self._active_meeting_id:
            return {
                "is_recording": False,
                "meeting_id": None,
                "status": "idle",
                "duration_seconds": 0,
                "segment_count": 0,
                "error": None,
            }

        session = self._sessions.get(self._active_meeting_id)
        if not session:
            return {
                "is_recording": False,
                "meeting_id": None,
                "status": "idle",
                "duration_seconds": 0,
                "segment_count": 0,
                "error": None,
            }

        return {
            "is_recording": session.is_active,
            "meeting_id": self._active_meeting_id,
            "status": "recording" if session.is_active else "stopped",
            "duration_seconds": session.duration_seconds,
            "segment_count": session.segment_count,
            "error": session.error,
        }

    async def start_recording(
        self,
        meeting_id: str,
        device_index: Optional[int] = None,
        on_segment: Optional[Callable] = None,
    ) -> str:
        """Start a new recording session. Returns device name."""
        if self._active_meeting_id:
            raise RuntimeError(
                f"Already recording meeting {self._active_meeting_id}. Stop it first."
            )

        provider = self._get_provider()
        session = RecordingSession(
            meeting_id=meeting_id,
            transcription_provider=provider,
            sample_rate=settings.audio_sample_rate,
            on_segment=on_segment,
        )

        device_name = await session.start(device_index=device_index)
        self._sessions[meeting_id] = session
        self._active_meeting_id = meeting_id

        return device_name

    async def stop_recording(self) -> dict:
        """Stop the active recording session."""
        if not self._active_meeting_id:
            raise RuntimeError("No active recording")

        session = self._sessions.get(self._active_meeting_id)
        if not session:
            raise RuntimeError("Session not found")

        result = await session.stop()
        meeting_id = self._active_meeting_id
        self._active_meeting_id = None

        return {"meeting_id": meeting_id, **result}


# Singleton instance
recording_manager = RecordingManager()
