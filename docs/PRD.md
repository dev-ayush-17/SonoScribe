# SonoScribe — Product Requirements Document

## Vision
A local-first meeting recorder and transcription app. Users manually start/stop recording during a meeting, audio is captured and transcribed continuously, and timestamped transcript segments are saved locally in SQLite. After the meeting, users can request AI-generated summaries, decisions, action items, owners, and dates.

## Target Users
Developers, engineers, and knowledge workers who want a private, local-first tool to record meetings and produce searchable transcripts — without relying on platform-specific bots or cloud-only solutions.

## Core Principles
1. **Local-first**: All data stays on the user's machine by default. Cloud providers are opt-in.
2. **Honest UX**: Never fake a recording or transcript. Show clear states.
3. **Pipeline modularity**: Audio capture, VAD, chunking, transcription, and persistence are independently testable.
4. **Provider abstraction**: Transcription and AI providers are swappable via configuration.

## Architecture

### Frontend
- React + TypeScript (Vite)
- Clean developer-tool aesthetic (Linear/Vercel-inspired)
- Dark neutral palette, Inter/Geist fonts, Lucide icons

### Backend
- FastAPI (Python 3.12)
- SQLite via SQLAlchemy (async with aiosqlite)
- Alembic migrations
- WebSocket for real-time transcript streaming to frontend

### Audio Pipeline (Backend)
```
System loopback audio (+ optional mic)
  → Voice Activity Detection (WebRTC VAD / silero-vad)
  → 15-30s chunks with ~1-2s overlap
  → Transcription provider (faster-whisper / Groq STT)
  → Timestamped SQLite segments
```

### AI Notes Pipeline
```
Transcript segments → chunk if long → LLM provider (Groq / Ollama / Gemini)
  → Structured output: summary, decisions, action items, open questions
  → Stored alongside meeting
```

## Features (MVP Priority Order)

### P0 — Must Have
1. **Recording start/stop** with clear UI state (idle → recording → stopped)
2. **System audio capture** on Windows (via sounddevice WASAPI loopback)
3. **Optional microphone input** (mixed or separate channel)
4. **Chunked transcription** via provider interface
5. **Timestamped transcript persistence** in SQLite
6. **Meeting list view** — browse past meetings
7. **Meeting detail view** — timestamped transcript, metadata
8. **Transcript export** (plain text, Markdown)

### P1 — Should Have
9. **On-demand AI notes** (summary, decisions, action items)
10. **Provider configuration UI** — select transcription/AI providers
11. **User consent/confirmation** before recording starts
12. **Error recovery** — retry failed chunks, queue persistence

### P2 — Nice to Have
13. **Search across transcripts**
14. **Audio playback** (if raw audio retention enabled)
15. **Keyboard shortcuts** for recording control

## Non-Goals
- Meeting auto-join bots
- Multi-user collaboration
- Real-time collaboration
- Mobile app
- Video capture

## Platform Support
- **Primary**: Windows 10/11 (WASAPI loopback for system audio)
- **Secondary**: macOS (CoreAudio, requires user setup)
- **Limited**: Linux (PulseAudio monitor source)

## Data Model
See `memory/PROJECT.md` for schema details.

## Security & Privacy
- No raw audio stored by default (configurable)
- API keys in `.env`, never in source
- No telemetry or external data transmission unless user configures a cloud provider
- Transcripts logged at DEBUG level only, never at INFO/WARNING
