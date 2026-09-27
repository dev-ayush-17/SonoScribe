# SonoScribe

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fdev-ayush-17%2FSonoScribe&env=DATABASE_URL,AUDIO_SAMPLE_RATE,STORE_RAW_AUDIO,AUDIO_STORAGE_DIR,TRANSCRIPTION_PROVIDER,FASTER_WHISPER_MODEL,FASTER_WHISPER_COMPUTE_TYPE,FASTER_WHISPER_DEVICE,GROQ_API_KEY,GROQ_TRANSCRIPTION_MODEL,AI_PROVIDER,HUGGINGFACE_API_KEY,HUGGINGFACE_MODEL,GROQ_AI_MODEL,OLLAMA_BASE_URL,OLLAMA_MODEL,GEMINI_API_KEY,GEMINI_MODEL,HOST,PORT,CORS_ORIGINS,LOG_LEVEL&envDescription=API%20keys%20and%20configurations%20needed%20to%20run%20SonoScribe&envLink=https%3A%2F%2Fgithub.com%2Fdev-ayush-17%2FSonoScribe%2Fblob%2Fmain%2FSETUP.md)

A local-first meeting recorder, Chrome Extension tab audio capture engine, and AI meeting notes suite. Capture system audio or live meeting tabs (Google Meet, Zoom Web), transcribe continuously in 1-minute chunks, generate windowed executive summaries, action items, and export `.ics` calendar events.

---

## 1. Try It Live
- **Live Vercel Application**: [https://frontend-eight-snowy-82.vercel.app](https://frontend-eight-snowy-82.vercel.app)
- **Live Render Docker Service**: [https://sonoscribe-api-xw35.onrender.com](https://sonoscribe-api-xw35.onrender.com)
- **Local Dev Instance**: [http://localhost:5173](http://localhost:5173)



---

## 2. Deploy Your Own Free Copy

Click the button below to deploy your own instance of SonoScribe in one click:

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fdev-ayush-17%2FSonoScribe&env=DATABASE_URL,AUDIO_SAMPLE_RATE,STORE_RAW_AUDIO,AUDIO_STORAGE_DIR,TRANSCRIPTION_PROVIDER,FASTER_WHISPER_MODEL,FASTER_WHISPER_COMPUTE_TYPE,FASTER_WHISPER_DEVICE,GROQ_API_KEY,GROQ_TRANSCRIPTION_MODEL,AI_PROVIDER,HUGGINGFACE_API_KEY,HUGGINGFACE_MODEL,GROQ_AI_MODEL,OLLAMA_BASE_URL,OLLAMA_MODEL,GEMINI_API_KEY,GEMINI_MODEL,HOST,PORT,CORS_ORIGINS,LOG_LEVEL&envDescription=API%20keys%20and%20configurations%20needed%20to%20run%20SonoScribe&envLink=https%3A%2F%2Fgithub.com%2Fdev-ayush-17%2FSonoScribe%2Fblob%2Fmain%2FSETUP.md)

For detailed descriptions of each required environment variable and step-by-step instructions on obtaining free Groq, Hugging Face, or Gemini API keys, refer to the [**SETUP.md Guide**](SETUP.md).

---

## 3. Run Locally with Docker

You can run the entire application (Frontend + Backend API) inside Docker using `docker compose`:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/dev-ayush-17/SonoScribe.git
   cd SonoScribe
   ```

2. **Configure environment variables**:
   ```bash
   cp .env.example .env
   ```

3. **Start the container**:
   ```bash
   docker compose up --build
   ```

4. **Access the application**:
   - Web App: [http://localhost:3000](http://localhost:3000)
   - API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 4. Manual Installation & Development (Advanced / Contributors)

### Prerequisites
- Python 3.12+
- Node.js 18+
- Windows 10/11 (for system audio capture) or Chrome Browser (for Extension tab capture)

### Backend Setup
```bash
cd backend
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
# source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env

# Run FastAPI Server
uvicorn app.main:app --reload --reload-dir app --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Chrome Extension Installation (`/extension`)
1. Open Google Chrome and navigate to `chrome://extensions`.
2. Enable **Developer mode** in the top-right toggle.
3. Click **Load unpacked** and select the `/extension` directory in this repository.
4. Click the **SonoScribe** extension icon on any Google Meet or Zoom tab, click **Start Capturing Tab**, and click **Stop and Transcribe** when done.

---

## Features
- **System & Tab Audio Capture**: Windows WASAPI loopback system capture + Manifest V3 Chrome Extension tab capture.
- **Audio Passthrough**: Hear your call audio normally while it's captured in real time.
- **Continuous 1-Minute Chunking**: Audio captured in 1-minute blocks with 5s overlap.
- **Rolling AI Notes Windowing**: 20–25 minute sliding windows for executive summaries, key decisions, action items, and future proposals.
- **.ics Calendar Export**: One-click iCalendar export for calendar integration.
- **Multi-Provider AI & Transcription**: Local `faster-whisper`, Groq Cloud STT, Hugging Face, Ollama, and Gemini LLMs.

---

## Architecture
- **Backend**: FastAPI + SQLAlchemy (async) + SQLite
- **Frontend**: React + TypeScript + Vite + GSAP
- **Chrome Extension**: Manifest V3 + Web Audio PCM Encoder
- **Transcription**: `faster-whisper` (local) / Groq STT (cloud)
- **AI Notes**: Hugging Face / Groq / Ollama / Gemini

---

## License
MIT
