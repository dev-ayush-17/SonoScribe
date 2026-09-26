"""Transcription provider interface and implementations."""

from __future__ import annotations

import asyncio
import io
import logging
import tempfile
import time
import wave
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class TranscriptionResult:
    """Result from a transcription provider."""
    text: str
    start_time: float
    end_time: float
    confidence: Optional[float] = None
    language: str = "en"
    provider: str = ""
    model: str = ""


class TranscriptionProvider(ABC):
    """Abstract base class for transcription providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name identifier."""
        ...

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Whether the provider is currently available."""
        ...

    @abstractmethod
    async def transcribe(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        language: str = "en",
    ) -> List[TranscriptionResult]:
        """Transcribe audio data and return results.

        Args:
            audio_data: Audio samples as float32 numpy array
            sample_rate: Sample rate in Hz
            language: Language code

        Returns:
            List of transcription results with timestamps
        """
        ...

    def _audio_to_wav_bytes(self, audio_data: np.ndarray, sample_rate: int) -> bytes:
        """Convert numpy audio to WAV bytes for providers that need files."""
        # Normalize to int16
        audio_int16 = (audio_data * 32767).astype(np.int16)
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # int16
            wf.setframerate(sample_rate)
            wf.writeframes(audio_int16.tobytes())
        return buffer.getvalue()

    def _save_temp_wav(self, audio_data: np.ndarray, sample_rate: int) -> str:
        """Save audio to a temporary WAV file. Caller must clean up."""
        wav_bytes = self._audio_to_wav_bytes(audio_data, sample_rate)
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp.write(wav_bytes)
        tmp.close()
        return tmp.name


class FasterWhisperProvider(TranscriptionProvider):
    """Local transcription using faster-whisper."""

    def __init__(self, model_size: str = "base.en", device: str = "cpu", compute_type: str = "int8"):
        self._model_size = model_size
        self._device = device
        self._compute_type = compute_type
        self._model = None
        self._available: Optional[bool] = None

    @property
    def name(self) -> str:
        return "faster-whisper"

    @property
    def is_available(self) -> bool:
        if self._available is not None:
            return self._available
        try:
            from faster_whisper import WhisperModel  # noqa: F401
            self._available = True
        except ImportError:
            self._available = False
        return self._available

    def _get_model(self):
        """Lazy-load the whisper model."""
        if self._model is None:
            from faster_whisper import WhisperModel
            logger.info(
                "Loading faster-whisper model: %s (device=%s, compute=%s)",
                self._model_size, self._device, self._compute_type,
            )
            self._model = WhisperModel(
                self._model_size,
                device=self._device,
                compute_type=self._compute_type,
            )
        return self._model

    async def transcribe(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        language: str = "en",
    ) -> List[TranscriptionResult]:
        if not self.is_available:
            raise RuntimeError("faster-whisper not installed")

        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._transcribe_sync, audio_data, sample_rate, language
        )

    def _transcribe_sync(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        language: str,
    ) -> List[TranscriptionResult]:
        model = self._get_model()

        # faster-whisper expects float32 audio at any sample rate
        segments_iter, info = model.transcribe(
            audio_data,
            language=language if not language.endswith(".en") else None,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(
                min_silence_duration_ms=500,
                speech_pad_ms=200,
            ),
        )

        results = []
        for segment in segments_iter:
            text = segment.text.strip()
            if text:
                results.append(TranscriptionResult(
                    text=text,
                    start_time=segment.start,
                    end_time=segment.end,
                    confidence=segment.avg_log_prob if hasattr(segment, 'avg_log_prob') else None,
                    language=info.language if info else language,
                    provider="faster-whisper",
                    model=self._model_size,
                ))

        return results


class GroqTranscriptionProvider(TranscriptionProvider):
    """Cloud transcription using Groq's Whisper API."""

    def __init__(self, api_key: str, model: str = "whisper-large-v3"):
        self._api_key = api_key
        self._model = model

    @property
    def name(self) -> str:
        return "groq"

    @property
    def is_available(self) -> bool:
        return bool(self._api_key)

    async def transcribe(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        language: str = "en",
    ) -> List[TranscriptionResult]:
        if not self.is_available:
            raise RuntimeError("Groq API key not configured")

        try:
            from groq import Groq
        except ImportError:
            raise RuntimeError("groq package not installed. Run: pip install groq")

        # Save to temp file (Groq API needs a file)
        tmp_path = self._save_temp_wav(audio_data, sample_rate)

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self._transcribe_sync, tmp_path, language
            )
            return result
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def _transcribe_sync(self, wav_path: str, language: str) -> List[TranscriptionResult]:
        from groq import Groq

        client = Groq(api_key=self._api_key)

        with open(wav_path, "rb") as f:
            response = client.audio.transcriptions.create(
                file=f,
                model=self._model,
                response_format="verbose_json",
                language=language,
                timestamp_granularities=["segment"],
            )

        results = []
        if hasattr(response, "segments") and response.segments:
            for seg in response.segments:
                text = seg.get("text", "").strip() if isinstance(seg, dict) else seg.text.strip()
                if text:
                    start = seg.get("start", 0) if isinstance(seg, dict) else seg.start
                    end = seg.get("end", 0) if isinstance(seg, dict) else seg.end
                    results.append(TranscriptionResult(
                        text=text,
                        start_time=start,
                        end_time=end,
                        provider="groq",
                        model=self._model,
                        language=language,
                    ))
        elif hasattr(response, "text") and response.text:
            results.append(TranscriptionResult(
                text=response.text.strip(),
                start_time=0,
                end_time=0,
                provider="groq",
                model=self._model,
                language=language,
            ))

        return results


def create_transcription_provider(
    provider_name: str,
    model: str = "base.en",
    device: str = "cpu",
    compute_type: str = "int8",
    api_key: str = "",
    groq_model: str = "whisper-large-v3",
) -> TranscriptionProvider:
    """Factory function to create a transcription provider.

    Args:
        provider_name: 'faster-whisper' or 'groq'
        model: Model name/size for faster-whisper
        device: Device for faster-whisper ('cpu' or 'cuda')
        compute_type: Compute type for faster-whisper
        api_key: API key for Groq
        groq_model: Model name for Groq

    Returns:
        A TranscriptionProvider instance
    """
    if provider_name == "faster-whisper":
        return FasterWhisperProvider(
            model_size=model,
            device=device,
            compute_type=compute_type,
        )
    elif provider_name == "groq":
        return GroqTranscriptionProvider(api_key=api_key, model=groq_model)
    else:
        raise ValueError(f"Unknown transcription provider: {provider_name}")
