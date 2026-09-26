# SonoScribe

A local-first meeting recorder and transcription app. Capture system audio, transcribe continuously, and save timestamped transcript segments locally. Optionally generate AI summaries, decisions, and action items.

## Features
- Manual start/stop recording with clear state indication
- System audio capture (Windows WASAPI loopback)
- Optional microphone input
- Real-time chunked transcription (faster-whisper local, Groq STT cloud opt-in)
- Timestamped transcript persistence in SQLite
- Meeting history and detail views
- Transcript export (text, markdown)
- On-demand AI notes (summary, decisions, action items, open questions)

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+
- Windows 10/11 (for system audio capture)

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Environment Configuration
Copy `backend/.env.example` to `backend/.env` and configure:

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | No | SQLite URL (default: `sqlite+aiosqlite:///./sonoscribe.db`) |
| `TRANSCRIPTION_PROVIDER` | No | `faster-whisper` (default) or `groq` |
| `FASTER_WHISPER_MODEL` | No | Model size (default: `base.en`) |
| `GROQ_API_KEY` | Only for Groq | Groq API key for cloud transcription/AI |
| `AI_PROVIDER` | No | `groq`, `ollama`, or `gemini` |
| `OLLAMA_BASE_URL` | Only for Ollama | Ollama server URL |
| `GEMINI_API_KEY` | Only for Gemini | Google Gemini API key |
| `STORE_RAW_AUDIO` | No | `true` to keep raw audio files (default: `false`) |

## Architecture
- **Backend**: FastAPI + SQLAlchemy (async) + SQLite
- **Frontend**: React + TypeScript + Vite
- **Audio**: sounddevice (WASAPI loopback on Windows)
- **Transcription**: faster-whisper (local) / Groq STT (cloud)
- **AI Notes**: LangChain with Groq / Ollama / Gemini providers

## Platform Support
| Platform | System Audio | Microphone | Notes |
|----------|-------------|------------|-------|
| Windows 10/11 | ✅ WASAPI loopback | ✅ | Primary target |
| macOS | ⚠️ Requires BlackHole/Soundflower | ✅ | User must set up virtual audio device |
| Linux | ⚠️ PulseAudio monitor | ✅ | Requires PulseAudio |

## License
MIT
