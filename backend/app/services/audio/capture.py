"""Audio capture service — robust system audio & microphone capture with automatic resampling and device fallback."""

from __future__ import annotations

import asyncio
import logging
import platform
import time
from collections import deque
from dataclasses import dataclass
from typing import Callable, Deque, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class AudioChunk:
    """A chunk of audio data ready for transcription."""
    data: np.ndarray
    sample_rate: int
    start_time: float  # seconds from recording start
    end_time: float
    chunk_index: int


@dataclass
class AudioDeviceInfo:
    """Information about an audio device."""
    index: int
    name: str
    max_input_channels: int
    max_output_channels: int
    default_sample_rate: float
    is_loopback: bool = False
    hostapi_name: str = ""


class AudioCaptureService:
    """Captures system audio or microphone input with auto-resampling to 16kHz and fail-safe fallback."""

    def __init__(
        self,
        sample_rate: int = 16000,
        chunk_duration: float = 60.0,  # 1 minute per chunk
        overlap_duration: float = 5.0,  # 5 seconds overlap
        on_chunk: Optional[Callable[[AudioChunk], None]] = None,
    ):
        self.sample_rate = sample_rate
        self.chunk_duration = chunk_duration
        self.overlap_duration = overlap_duration
        self.on_chunk = on_chunk

        self._is_recording = False
        self._stream = None
        self._buffer: List[np.ndarray] = []
        self._start_time: float = 0.0
        self._chunk_index: int = 0
        self._samples_captured: int = 0
        self._device_index: Optional[int] = None
        self._device_name: str = ""
        self._native_sample_rate: int = 16000
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        # Bounded chunk queue for producer-consumer
        self._chunk_queue: Deque[AudioChunk] = deque(maxlen=100)

    @property
    def is_recording(self) -> bool:
        return self._is_recording

    @property
    def elapsed_seconds(self) -> float:
        if not self._is_recording:
            return 0.0
        return time.monotonic() - self._start_time

    @property
    def device_name(self) -> str:
        return self._device_name

    @staticmethod
    def list_devices() -> List[AudioDeviceInfo]:
        """List available, cleaned input devices (filtering out WDM-KS/Mapper entries)."""
        try:
            import sounddevice as sd
        except ImportError:
            logger.warning("sounddevice not installed")
            return []

        devices = []
        hostapis = sd.query_hostapis()

        for i, dev in enumerate(sd.query_devices()):
            hostapi_name = ""
            if dev.get("hostapi") is not None:
                hostapi_name = hostapis[dev["hostapi"]]["name"]

            # Filter out WDM-KS devices as they fail with blocking API unsupported
            if "wdm-ks" in hostapi_name.lower():
                continue

            # Filter out duplicate sound mappers
            name = dev["name"]
            if "sound mapper" in name.lower() or "primary sound" in name.lower():
                continue

            # Only include devices that support input channels > 0
            if dev["max_input_channels"] > 0:
                devices.append(AudioDeviceInfo(
                    index=i,
                    name=dev["name"],
                    max_input_channels=dev["max_input_channels"],
                    max_output_channels=dev["max_output_channels"],
                    default_sample_rate=dev["default_samplerate"],
                    is_loopback=False,
                    hostapi_name=hostapi_name,
                ))

        return devices

    @staticmethod
    def get_default_device() -> Optional[AudioDeviceInfo]:
        """Find the default input audio device."""
        devices = AudioCaptureService.list_devices()
        if devices:
            return devices[0]
        return None

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info, status):
        """Callback invoked by sounddevice for each audio block."""
        if status:
            logger.warning("Audio stream status: %s", status)
        if not self._is_recording:
            return

        # Flatten/average to mono
        if indata.ndim > 1:
            audio_data = indata.mean(axis=1)
        else:
            audio_data = indata.flatten()

        audio_data = audio_data.astype(np.float32)

        # Software resample to target sample rate (16000 Hz) if native rate differs
        if self._native_sample_rate != self.sample_rate and len(audio_data) > 0:
            duration = len(audio_data) / self._native_sample_rate
            target_len = int(duration * self.sample_rate)
            if target_len > 0:
                x_orig = np.linspace(0, duration, len(audio_data), endpoint=False)
                x_target = np.linspace(0, duration, target_len, endpoint=False)
                audio_data = np.interp(x_target, x_orig, audio_data).astype(np.float32)

        self._buffer.append(audio_data)
        self._samples_captured += len(audio_data)

        # Check if we have enough samples for a chunk (at target 16kHz)
        chunk_samples = int(self.chunk_duration * self.sample_rate)
        total_buffered = sum(len(b) for b in self._buffer)

        if total_buffered >= chunk_samples:
            full_audio = np.concatenate(self._buffer)

            # Extract chunk
            chunk_data = full_audio[:chunk_samples]
            chunk_start = (self._chunk_index * (self.chunk_duration - self.overlap_duration))
            chunk_end = chunk_start + self.chunk_duration

            chunk = AudioChunk(
                data=chunk_data.astype(np.float32),
                sample_rate=self.sample_rate,
                start_time=chunk_start,
                end_time=chunk_end,
                chunk_index=self._chunk_index,
            )

            # Keep overlap for next chunk
            overlap_samples = int(self.overlap_duration * self.sample_rate)
            remaining = full_audio[chunk_samples - overlap_samples:]
            self._buffer = [remaining]
            self._chunk_index += 1

            self._chunk_queue.append(chunk)

            if self.on_chunk and self._loop:
                self._loop.call_soon_threadsafe(self.on_chunk, chunk)

    async def start(self, device_index: Optional[int] = None) -> str:
        """Start audio capture. Returns the device name used."""
        if self._is_recording:
            raise RuntimeError("Already recording")

        try:
            import sounddevice as sd
        except ImportError:
            raise RuntimeError("sounddevice not installed. Run: pip install sounddevice")

        self._loop = asyncio.get_event_loop()

        # Validate requested device index
        target_idx = device_index
        if target_idx is not None:
            try:
                dev_info = sd.query_devices(target_idx)
                if dev_info.get("max_input_channels", 0) == 0:
                    logger.warning("Requested device %d has 0 input channels. Falling back to default input.", target_idx)
                    target_idx = None
            except Exception as e:
                logger.warning("Invalid device index %s (%s). Falling back to default input.", target_idx, e)
                target_idx = None

        if target_idx is None:
            default_dev = self.get_default_device()
            if default_dev:
                target_idx = default_dev.index
            else:
                target_idx = sd.default.device[0]

        dev_info = sd.query_devices(target_idx)
        self._device_index = target_idx
        self._device_name = dev_info["name"]

        self._native_sample_rate = int(dev_info.get("default_samplerate", 16000))
        max_in = dev_info.get("max_input_channels", 1)
        channels = max(1, min(max_in, 2))

        logger.info(
            "Starting audio stream on device '%s' (index=%s, native_sr=%d, channels=%d)",
            self._device_name, self._device_index, self._native_sample_rate, channels,
        )

        # Reset state
        self._buffer = []
        self._chunk_index = 0
        self._samples_captured = 0
        self._chunk_queue.clear()
        self._start_time = time.monotonic()
        self._is_recording = True

        # Fail-safe stream opening
        try:
            self._stream = sd.InputStream(
                device=self._device_index,
                samplerate=self._native_sample_rate,
                channels=channels,
                dtype="float32",
                callback=self._audio_callback,
                blocksize=int(self._native_sample_rate * 0.5),  # 500ms blocks
            )
            self._stream.start()
        except Exception as e:
            logger.warning("Failed to open audio stream on device %s: %s. Attempting fallback to default input.", self._device_index, e)
            try:
                def_idx = sd.default.device[0]
                dev_info = sd.query_devices(def_idx)
                self._device_index = def_idx
                self._device_name = dev_info["name"]
                self._native_sample_rate = int(dev_info.get("default_samplerate", 16000))
                channels = max(1, min(dev_info.get("max_input_channels", 1), 2))
                
                self._stream = sd.InputStream(
                    device=def_idx,
                    samplerate=self._native_sample_rate,
                    channels=channels,
                    dtype="float32",
                    callback=self._audio_callback,
                    blocksize=int(self._native_sample_rate * 0.5),
                )
                self._stream.start()
                logger.info("Fallback audio stream opened on device %s", self._device_name)
            except Exception as fallback_err:
                self._is_recording = False
                logger.error("Fallback audio stream failed: %s", fallback_err)
                raise RuntimeError(f"Failed to start audio stream: {fallback_err}") from fallback_err

        return self._device_name

    async def stop(self) -> List[AudioChunk]:
        """Stop audio capture. Returns any remaining buffered chunks."""
        if not self._is_recording:
            return []

        self._is_recording = False
        remaining_chunks = []

        if self._buffer:
            full_audio = np.concatenate(self._buffer)
            if len(full_audio) > self.sample_rate * 0.5:
                chunk_start = (self._chunk_index * (self.chunk_duration - self.overlap_duration))
                chunk_end = chunk_start + len(full_audio) / self.sample_rate

                chunk = AudioChunk(
                    data=full_audio.astype(np.float32),
                    sample_rate=self.sample_rate,
                    start_time=chunk_start,
                    end_time=chunk_end,
                    chunk_index=self._chunk_index,
                )
                remaining_chunks.append(chunk)
                self._chunk_queue.append(chunk)

        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception as e:
                logger.warning("Error stopping audio stream: %s", e)
            self._stream = None

        self._buffer = []
        return remaining_chunks

    def get_pending_chunks(self) -> List[AudioChunk]:
        """Get all pending chunks from the queue (non-blocking)."""
        chunks = []
        while self._chunk_queue:
            try:
                chunks.append(self._chunk_queue.popleft())
            except IndexError:
                break
        return chunks
