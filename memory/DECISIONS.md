# SonoScribe — Decisions Log

## 2026-09-27

### D001: Stack Choice — FastAPI + React/Vite
**Decision**: Use FastAPI (Python) backend + React/TypeScript frontend (Vite).
**Rationale**: 
- Python has the best audio processing ecosystem (sounddevice, faster-whisper, silero-vad)
- FastAPI already installed on system, supports WebSocket natively
- LangChain already installed for AI notes pipeline
- React+Vite is fast to scaffold and the user's spec suggests it

### D002: SQLite via SQLAlchemy async
**Decision**: Use SQLAlchemy async with aiosqlite for database.
**Rationale**: Local-first, no external DB server needed, migrations via Alembic, async for non-blocking IO.

### D003: Audio Capture — sounddevice with WASAPI loopback
**Decision**: Use `sounddevice` library with WASAPI loopback for system audio on Windows.
**Rationale**: 
- Windows-native, doesn't require virtual audio cable
- WASAPI loopback captures system output directly
- Can also capture microphone input on a separate stream
- Falls back gracefully on other platforms

### D004: Transcription Provider — faster-whisper primary, Groq STT fallback
**Decision**: Use faster-whisper as primary local provider, Groq STT as opt-in cloud fallback.
**Rationale**: 
- faster-whisper runs locally, no API keys needed
- Groq provides fast cloud inference when local GPU is unavailable
- Provider interface allows swapping without pipeline changes

### D005: AI Notes — LangChain with multiple providers
**Decision**: Use LangChain for AI notes with Groq, Ollama, and Gemini as provider options.
**Rationale**: 
- LangChain already installed on system
- Abstracts provider differences
- Supports structured output parsing
- User explicitly approved LangChain usage

### D006: No raw audio by default
**Decision**: Do not store raw audio unless user explicitly enables `STORE_RAW_AUDIO=true`.
**Rationale**: Privacy-first, reduce storage, audio is transcribed in-memory and discarded.

### D007: 60-Second Audio Chunking with 5-Second Overlap
**Decision**: Increase audio capture window from 20s to 60s (1 min) with 5s overlap.
**Rationale**: Provides full, meaningful sentence context per segment for long meeting recording.

### D008: Durable Raw Session Files & 20–25 Minute Rolling Windowed AI Artifacts
**Decision**: Save continuous raw transcript files (`meeting_docs/{id}/raw_transcript.txt`) and process AI notes in 20–25 minute rolling window blocks.
**Rationale**: Prevents LLM context window overflow on multi-hour meetings and produces clean multi-artifact outputs (Minutes of Meeting, Highlights, Action Items, Proposals & Schedules).
