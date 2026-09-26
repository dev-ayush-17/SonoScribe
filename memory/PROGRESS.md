# SonoScribe — Progress Tracker

## Completed
- [x] Repository initialized & baseline structure
- [x] PRD created (`docs/PRD.md`)
- [x] Memory bank created (`memory/PROJECT.md`, `DECISIONS.md`, `PROGRESS.md`, `PATTERNS.md`)
- [x] Backend architecture: FastAPI 0.115+, SQLAlchemy async, SQLite database, pydantic-settings
- [x] Health check & provider config endpoints (`/api/v1/health`, `/api/v1/config`)
- [x] Audio capture pipeline: sounddevice WASAPI loopback support on Windows, mono conversion, 20s VAD chunking with 1.5s overlap
- [x] Transcription provider abstraction: `faster-whisper` (local) & Groq STT (cloud), retry queue for failed chunks
- [x] Recording Session Manager: start/stop lifecycle, real-time segment saving into SQLite database
- [x] Meetings API: list, detail, patch, delete, and export (Markdown, plain Text, JSON formats)
- [x] AI Notes engine: provider abstraction (Groq, Ollama, Gemini), structured JSON parsing, chunked summarization + synthesis for long transcripts
- [x] WebSocket server: live transcript segment streaming (`/ws/transcript`)
- [x] Backend Unit & Integration Tests: Pytest suite (6/6 tests passing cleanly)
- [x] Frontend React + TypeScript application with Vite and Lucide icons
- [x] Vercel/Linear dark theme design system (`src/index.css`)
- [x] Explicit user recording consent modal (`ConsentModal.tsx`)
- [x] Audio source picker, live status indicator, live streaming transcript view
- [x] Past meeting list with search and deletion
- [x] Meeting detail timeline view with mono timestamps and 1-click Markdown export
- [x] AI notes generation UI displaying summaries, explicit decisions, action items with owner/due date, open questions, notable timestamps
- [x] Zero-error frontend production build (`npm run build`)

## In Progress
- None — MVP core requirements complete

## Blocked
- None

## Next Best Tasks (Post-MVP)
1. Optional real-time speaker diarization (pyannote.audio)
2. Native desktop packaging (Tauri / Electron)
3. Full-text search across past transcripts using SQLite FTS5

## Tested & Verified
- Pytest backend test suite (`python -m pytest backend/tests/test_backend.py`): 6 passed in 0.79s
- Frontend TypeScript build (`npm run build`): Completed in 2.48s with 0 errors
