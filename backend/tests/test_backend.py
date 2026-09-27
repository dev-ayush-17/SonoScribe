"""Unit and integration tests for SonoScribe backend."""

import pytest
import pytest_asyncio
import numpy as np
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.database import Base, get_db
from app.main import app
from app.models import Meeting, TranscriptSegment, AiNote
from app.services.audio.capture import AudioChunk, AudioCaptureService
from app.services.transcription.provider import (
    TranscriptionProvider,
    TranscriptionResult,
    create_transcription_provider,
)
from app.services.ai.notes import _parse_ai_response, _validate_notes, create_ai_provider
from app.api.meetings import _export_markdown, _export_text, _export_json, _format_timestamp

# Test SQLite memory DB engine
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


@pytest_asyncio.fixture(autouse=True)
async def prepare_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["ok", "degraded"]
        assert "platform" in data


@pytest.mark.asyncio
async def test_config_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/config")
        assert response.status_code == 200
        data = response.json()
        assert "transcription" in data
        assert "ai" in data


@pytest.mark.asyncio
async def test_meeting_crud_and_export():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create meeting via DB directly
        async with TestingSessionLocal() as db:
            meeting = Meeting(
                id="test-meeting-1",
                title="Sprint Planning & Architecture",
                started_at=datetime.now(timezone.utc),
                duration_seconds=125.0,
                status="completed",
                sample_rate=16000,
            )
            seg1 = TranscriptSegment(
                id="seg-1",
                meeting_id="test-meeting-1",
                segment_index=0,
                start_time=0.0,
                end_time=5.0,
                text="Welcome everyone to the sprint planning meeting.",
                provider="mock",
                model="mock-v1",
            )
            seg2 = TranscriptSegment(
                id="seg-2",
                meeting_id="test-meeting-1",
                segment_index=1,
                start_time=5.5,
                end_time=12.0,
                text="Alice will handle backend database migrations by Friday.",
                provider="mock",
                model="mock-v1",
            )
            db.add_all([meeting, seg1, seg2])
            await db.commit()

        # List meetings
        res = await ac.get("/api/v1/meetings")
        assert res.status_code == 200
        meetings = res.json()
        assert len(meetings) == 1
        assert meetings[0]["title"] == "Sprint Planning & Architecture"
        assert meetings[0]["segment_count"] == 2

        # Get meeting details
        res = await ac.get("/api/v1/meetings/test-meeting-1")
        assert res.status_code == 200
        detail = res.json()
        assert detail["id"] == "test-meeting-1"
        assert len(detail["segments"]) == 2

        # Test Markdown Export
        res = await ac.get("/api/v1/meetings/test-meeting-1/export?format=markdown")
        assert res.status_code == 200
        exp_data = res.json()
        assert "Welcome everyone" in exp_data["content"]
        assert "## Transcript" in exp_data["content"]

        # Test Text Export
        res = await ac.get("/api/v1/meetings/test-meeting-1/export?format=text")
        assert res.status_code == 200
        assert "[00:00] Welcome everyone" in res.json()["content"]

        # Test ICS Export
        res = await ac.get("/api/v1/meetings/test-meeting-1/export?format=ics")
        assert res.status_code == 200
        ics_content = res.json()["content"]
        assert "BEGIN:VCALENDAR" in ics_content
        assert "BEGIN:VEVENT" in ics_content
        assert "SUMMARY:Sprint Planning & Architecture" in ics_content
        assert "END:VCALENDAR" in ics_content

        # Update meeting
        res = await ac.patch("/api/v1/meetings/test-meeting-1", json={"title": "Updated Sprint Planning"})
        assert res.status_code == 200
        assert res.json()["title"] == "Updated Sprint Planning"

        # Delete meeting
        res = await ac.delete("/api/v1/meetings/test-meeting-1")
        assert res.status_code == 200
        res = await ac.get("/api/v1/meetings/test-meeting-1")
        assert res.status_code == 404


@pytest.mark.asyncio
async def test_upload_recording_endpoint():
    import io
    import wave
    sr = 16000
    samples = (np.sin(2 * np.pi * 440 * np.linspace(0, 0.5, sr // 2)) * 10000).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(samples.tobytes())
    wav_bytes = buf.getvalue()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        files = {"file": ("tab_audio.wav", wav_bytes, "audio/wav")}
        data = {"title": "Extension Google Meet Session"}
        res = await ac.post("/api/v1/recording/upload", files=files, data=data)
        assert res.status_code == 200
        res_json = res.json()
        assert res_json["status"] == "completed"
        assert res_json["title"] == "Extension Google Meet Session"
        assert "meeting_id" in res_json



def test_ai_response_parser():
    raw_json = """{
        "summary": "Discussed Q3 roadmap and team allocations.",
        "decisions": ["Adopt SQLite for local storage"],
        "action_items": [{"task": "Setup CI/CD pipeline", "owner": "Bob", "due_date": "2026-10-01"}],
        "open_questions": ["Will we need PostgreSQL for scaling?"],
        "notable_timestamps": ["02:15 - CI decision"]
    }"""
    parsed = _parse_ai_response(raw_json)
    assert parsed["summary"] == "Discussed Q3 roadmap and team allocations."
    assert parsed["decisions"] == ["Adopt SQLite for local storage"]
    assert len(parsed["action_items"]) == 1
    assert parsed["action_items"][0]["owner"] == "Bob"

    # Test markdown fenced code block response
    fenced_json = f"Here are the meeting notes:\n```json\n{raw_json}\n```\nHope this helps!"
    parsed_fenced = _parse_ai_response(fenced_json)
    assert parsed_fenced["summary"] == "Discussed Q3 roadmap and team allocations."

    # Test malformed fallback
    malformed = "Just plain text notes without json."
    parsed_malformed = _parse_ai_response(malformed)
    assert parsed_malformed["summary"] == malformed


def test_timestamp_formatting():
    assert _format_timestamp(0.0) == "00:00"
    assert _format_timestamp(65.0) == "01:05"
    assert _format_timestamp(3665.0) == "01:01:05"


class MockTranscriptionProvider(TranscriptionProvider):
    @property
    def name(self) -> str:
        return "mock"

    @property
    def is_available(self) -> bool:
        return True

    async def transcribe(self, audio_data: np.ndarray, sample_rate: int, language: str = "en"):
        return [
            TranscriptionResult(
                text="This is a mock transcription segment.",
                start_time=0.0,
                end_time=2.0,
                confidence=0.95,
                language="en",
                provider="mock",
                model="mock-v1",
            )
        ]


@pytest.mark.asyncio
async def test_mock_transcription_provider():
    provider = MockTranscriptionProvider()
    audio = np.zeros(16000, dtype=np.float32)
    results = await provider.transcribe(audio, 16000)
    assert len(results) == 1
    assert results[0].text == "This is a mock transcription segment."


def test_ai_provider_factory():
    hf_provider = create_ai_provider("huggingface")
    assert hf_provider is not None
    assert hf_provider.name == "huggingface"

    groq_provider = create_ai_provider("groq", api_key="dummy_key")
    assert groq_provider is not None
    assert groq_provider.name == "groq"

    ollama_provider = create_ai_provider("ollama")
    assert ollama_provider is not None
    assert ollama_provider.name == "ollama"

    gemini_provider = create_ai_provider("gemini", api_key="dummy_key")
    assert gemini_provider is not None
    assert gemini_provider.name == "gemini"

