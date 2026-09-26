"""Audio capture service — system loopback + optional mic on Windows (WASAPI)."""

from __future__ import annotations

import asyncio
import logging
import platform
import time
from collections import deque
from dataclasses import dataclass, field
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
    """Captures system audio (loopback) and optional microphone input.

    On Windows, uses WASAPI loopback to capture system audio output.
    On other platforms, attempts to use default input device.
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        chunk_duration: float = 20.0,  # seconds per chunk
        overlap_duration: float = 1.5,  # seconds overlap between chunks
        on_chunk: Optional[Callable[[AudioChunk], None]] = None,
    ):
        self.sample_rate = sample_rate
        self.chunk_duration = chunk_duration
        self.overlap_duration = overlap_duration
        self.on_chunk = on_chunk

        self._is_recording = False
        self._stream = None
        self._buffer: List[np.ndarray] = []
        self._buffer_lock = asyncio.Lock() if asyncio.get_event_loop_policy() else None
        self._start_time: float = 0.0
        self._chunk_index: int = 0
        self._samples_captured: int = 0
        self._device_index: Optional[int] = None
        self._device_name: str = ""
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
        """List available audio devices."""
        try:
            import sounddevice as sd
        except ImportError:
            logger.warning("sounddevice not installed")
            return []

        devices = []
        hostapis = sd.query_hostapis()
        wasapi_idx = None
        for i, api in enumerate(hostapis):
            if "wasapi" in api["name"].lower():
                wasapi_idx = i
                break

        for i, dev in enumerate(sd.query_devices()):
            is_loopback = False
            hostapi_name = ""
            if dev.get("hostapi") is not None:
                api_info = hostapis[dev["hostapi"]]
                hostapi_name = api_info["name"]
                # On Windows, WASAPI output devices can be used as loopback
                if wasapi_idx is not None and dev["hostapi"] == wasapi_idx:
                    if dev["max_output_channels"] > 0:
                        is_loopback = True

            devices.append(AudioDeviceInfo(
                index=i,
                name=dev["name"],
                max_input_channels=dev["max_input_channels"],
                max_output_channels=dev["max_output_channels"],
                default_sample_rate=dev["default_samplerate"],
                is_loopback=is_loopback,
                hostapi_name=hostapi_name,
            ))
        return devices

    @staticmethod
    def get_default_loopback_device() -> Optional[AudioDeviceInfo]:
        """Find the default system audio loopback device (Windows WASAPI)."""
        devices = AudioCaptureService.list_devices()
        # Prefer WASAPI loopback devices
        loopback_devices = [d for d in devices if d.is_loopback]
        if loopback_devices:
            # Prefer the default output device
            try:
                import sounddevice as sd
                default_output = sd.query_devices(kind="output")
                for dev in loopback_devices:
                    if dev.name == default_output["name"]:
                        return dev
            except Exception:
                pass
            return loopback_devices[0]

        # Fallback: any input device
        input_devices = [d for d in devices if d.max_input_channels > 0]
        if input_devices:
            return input_devices[0]
        return None

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info, status):
        """Callback invoked by sounddevice for each audio block."""
        if status:
            logger.warning("Audio stream status: %s", status)
        if not self._is_recording:
            return

        # Copy data to avoid buffer reuse issues
        audio_data = indata.copy()
        if audio_data.ndim > 1:
            # Convert to mono by averaging channels
            audio_data = audio_data.mean(axis=1)

        self._buffer.append(audio_data)
        self._samples_captured += len(audio_data)

        # Check if we have enough samples for a chunk
        chunk_samples = int(self.chunk_duration * self.sample_rate)
        total_buffered = sum(len(b) for b in self._buffer)

        if total_buffered >= chunk_samples:
            # Concatenate buffer
            full_audio = np.concatenate(self._buffer)

            # Extract chunk
            chunk_data = full_audio[:chunk_samples]
            current_time = time.monotonic()
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

            # Add to queue
            self._chunk_queue.append(chunk)

            # Notify callback
            if self.on_chunk and self._loop:
                self._loop.call_soon_threadsafe(self.on_chunk, chunk)

    async def start(self, device_index: Optional[int] = None) -> str:
        """Start audio capture. Returns the device name used."""
        if self._is_recording:
            raise RuntimeError("Already recording")

        try:
            import sounddevice as sd
        except ImportError:
            raise RuntimeError(
                "sounddevice not installed. Run: pip install sounddevice"
            )

        self._loop = asyncio.get_event_loop()

        # Select device
        if device_index is not None:
            device = sd.query_devices(device_index)
            self._device_index = device_index
            self._device_name = device["name"]
        else:
            # Try to find loopback device
            loopback = self.get_default_loopback_device()
            if loopback:
                self._device_index = loopback.index
                self._device_name = loopback.name
            else:
                # Use default input
                self._device_index = None
                self._device_name = "Default input"

        logger.info("Starting audio capture on device: %s", self._device_name)

        # Determine channels
        if self._device_index is not None:
            dev_info = sd.query_devices(self._device_index)
            channels = max(1, min(dev_info.get("max_input_channels", 0),
                                   dev_info.get("max_output_channels", 0), 2))
            if channels == 0:
                # For loopback (output) devices, use max_output_channels
                channels = min(dev_info.get("max_output_channels", 1), 2)
        else:
            channels = 1

        channels = max(1, channels)

        # Reset state
        self._buffer = []
        self._chunk_index = 0
        self._samples_captured = 0
        self._chunk_queue.clear()
        self._start_time = time.monotonic()
        self._is_recording = True

        try:
            # On Windows with WASAPI loopback, we need special handling
            is_wasapi_loopback = False
            if platform.system() == "Windows" and self._device_index is not None:
                dev_info = sd.query_devices(self._device_index)
                hostapis = sd.query_hostapis()
                if dev_info.get("hostapi") is not None:
                    api = hostapis[dev_info["hostapi"]]
                    if "wasapi" in api["name"].lower() and dev_info["max_output_channels"] > 0:
                        is_wasapi_loopback = True

            if is_wasapi_loopback:
                # WASAPI loopback: open output device as input with wasapi exclusive
                import sounddevice as sd
                self._stream = sd.InputStream(
                    device=self._device_index,
                    samplerate=self.sample_rate,
                    channels=channels,
                    dtype="float32",
                    callback=self._audio_callback,
                    blocksize=int(self.sample_rate * 0.5),  # 500ms blocks
                    extra_settings=sd.WasapiSettings(exclusive=False),
                )
            else:
                self._stream = sd.InputStream(
                    device=self._device_index,
                    samplerate=self.sample_rate,
                    channels=channels,
                    dtype="float32",
                    callback=self._audio_callback,
                    blocksize=int(self.sample_rate * 0.5),
                )
            self._stream.start()
        except Exception as e:
            self._is_recording = False
            raise RuntimeError(f"Failed to start audio stream: {e}") from e

        return self._device_name

    async def stop(self) -> List[AudioChunk]:
        """Stop audio capture. Returns any remaining buffered chunks."""
        if not self._is_recording:
            return []

        self._is_recording = False
        remaining_chunks = []

        # Flush remaining buffer as final chunk
        if self._buffer:
            full_audio = np.concatenate(self._buffer)
            if len(full_audio) > self.sample_rate * 0.5:  # Only if > 0.5s
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

        # Stop and close stream
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
