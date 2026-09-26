# SonoScribe — Project Overview

## Goals
Build a local-first meeting recorder and transcription app as a hackathon MVP. The core flow is:
**Start recording → Capture audio → Transcribe continuously → Save segments → (Optional) AI summary**

## Scope
- Manual start/stop recording
- System audio capture (Windows WASAPI loopback primary)
- Chunked transcription with provider abstraction
- SQLite persistence with migrations
- Meeting history / detail views
- Transcript export (text, markdown)
- On-demand AI notes (Groq / Ollama / Gemini)

## Architecture

### Stack
| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + TypeScript, Vite, Lucide icons |
| Backend | FastAPI, Python 3.12 |
| Database | SQLite via SQLAlchemy (async, aiosqlite) |
| Migrations | Alembic |
| Audio | sounddevice (WASAPI loopback on Windows) |
| VAD | silero-vad or webrtcvad |
| Transcription | faster-whisper (local), Groq STT (cloud, opt-in) |
| AI Notes | LangChain + Groq / Ollama / Gemini |
| Real-time | WebSocket (FastAPI native) |

### Directory Structure
```
SonoScribe/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry
│   │   ├── config.py            # Centralized config from env
│   │   ├── database.py          # SQLAlchemy setup
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── api/                 # Route handlers
│   │   │   ├── meetings.py
│   │   │   ├── recording.py
│   │   │   ├── transcription.py
│   │   │   └── ai_notes.py
│   │   ├── services/            # Business logic
│   │   │   ├── audio/           # Audio capture, VAD, chunking
│   │   │   ├── transcription/   # Provider interface + impls
│   │   │   ├── ai/              # AI notes provider interface
│   │   │   └── export/          # Transcript export
│   │   └── core/                # Shared utilities
│   ├── alembic/                 # DB migrations
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── types/
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
├── docs/
│   └── PRD.md
├── memory/
│   ├── PROJECT.md
│   ├── DECISIONS.md
│   ├── PROGRESS.md
│   └── PATTERNS.md
└── README.md
```

### Data Model
```sql
-- meetings table
CREATE TABLE meetings (
    id TEXT PRIMARY KEY,           -- UUID
    title TEXT NOT NULL,
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP,
    duration_seconds REAL,
    status TEXT NOT NULL DEFAULT 'recording',  -- recording|completed|failed
    audio_device TEXT,
    sample_rate INTEGER DEFAULT 16000,
    raw_audio_path TEXT,           -- NULL unless user enables retention
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- transcript_segments table
CREATE TABLE transcript_segments (
    id TEXT PRIMARY KEY,           -- UUID
    meeting_id TEXT NOT NULL REFERENCES meetings(id),
    segment_index INTEGER NOT NULL,
    start_time REAL NOT NULL,      -- seconds from meeting start
    end_time REAL NOT NULL,
    text TEXT NOT NULL,
    confidence REAL,
    provider TEXT NOT NULL,        -- e.g. 'faster-whisper', 'groq'
    model TEXT,                    -- e.g. 'base.en', 'whisper-large-v3'
    status TEXT NOT NULL DEFAULT 'final',  -- pending|processing|final|failed
    language TEXT DEFAULT 'en',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ai_notes table
CREATE TABLE ai_notes (
    id TEXT PRIMARY KEY,
    meeting_id TEXT NOT NULL REFERENCES meetings(id),
    provider TEXT NOT NULL,
    model TEXT,
    summary TEXT,
    decisions TEXT,                -- JSON array
    action_items TEXT,             -- JSON array [{task, owner, due_date}]
    open_questions TEXT,           -- JSON array
    notable_timestamps TEXT,       -- JSON array
    raw_response TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Setup
See `README.md` for full setup instructions.

### Quick Start
```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your config
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

## Ports
- Backend API: `http://localhost:8000`
- Frontend: `http://localhost:5173`
