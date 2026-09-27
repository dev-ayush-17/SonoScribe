# SonoScribe Environment Variables Setup Guide

This guide details all environment variables used by **SonoScribe**, what each variable is for, and exact step-by-step instructions on how to obtain API keys for free AI and cloud transcription providers.

---

## Environment Variables Reference

### 1. Database Configuration
- **`DATABASE_URL`**
  - **Purpose**: SQLAlchemy connection string for database persistence (SQLite by default or PostgreSQL).
  - **Default**: `sqlite+aiosqlite:///./sonoscribe.db`
  - **How to obtain**: For default local storage, no setup required. For PostgreSQL / Supabase, copy the connection string from your database dashboard settings.

### 2. Audio Capture Settings
- **`AUDIO_SAMPLE_RATE`**
  - **Purpose**: Sample rate in Hz for input audio capture.
  - **Default**: `16000`
- **`STORE_RAW_AUDIO`**
  - **Purpose**: Toggle persisting raw WAV files on disk (`true` or `false`).
  - **Default**: `false`
- **`AUDIO_STORAGE_DIR`**
  - **Purpose**: Directory path for raw audio files.
  - **Default**: `./audio_storage`

### 3. Speech-to-Text / Transcription Engine
- **`TRANSCRIPTION_PROVIDER`**
  - **Purpose**: Active transcription provider (`faster-whisper` for local CPU/GPU, or `groq` for ultra-fast cloud Whisper).
  - **Default**: `faster-whisper`
- **`FASTER_WHISPER_MODEL`**
  - **Purpose**: Model size for local faster-whisper (`tiny.en`, `base.en`, `small.en`, `medium.en`, `large-v3`).
  - **Default**: `base.en`
- **`FASTER_WHISPER_COMPUTE_TYPE`**
  - **Purpose**: Quantization compute type (`int8`, `float16`, `float32`).
  - **Default**: `int8`
- **`FASTER_WHISPER_DEVICE`**
  - **Purpose**: Device for faster-whisper execution (`cpu` or `cuda`).
  - **Default**: `cpu`
- **`GROQ_API_KEY`**
  - **Purpose**: API Key for Groq Cloud Speech-to-Text (Whisper-large-v3) and AI Note synthesis.
  - **Default**: `""`
  - **How to obtain**:
    1. Visit [Groq Console](https://console.groq.com/keys).
    2. Sign up or log in with your account.
    3. Click **"Create API Key"**, copy the generated key string, and paste it as `GROQ_API_KEY`.
- **`GROQ_TRANSCRIPTION_MODEL`**
  - **Purpose**: Groq Whisper model name.
  - **Default**: `whisper-large-v3`

### 4. AI Notes & Meeting Summary Providers
- **`AI_PROVIDER`**
  - **Purpose**: Active AI provider for automated meeting notes synthesis (`huggingface`, `groq`, `ollama`, `gemini`, or `none`).
  - **Default**: `huggingface`
- **`HUGGINGFACE_API_KEY`**
  - **Purpose**: Hugging Face User Access Token for Serverless Inference API.
  - **Default**: `""`
  - **How to obtain**:
    1. Go to [Hugging Face Access Tokens](https://huggingface.co/settings/tokens).
    2. Log in or create a free account.
    3. Click **"Create new token"**, set permissions to **Read**, copy the token (`hf_...`), and paste as `HUGGINGFACE_API_KEY`.
- **`HUGGINGFACE_MODEL`**
  - **Purpose**: Hugging Face model repository ID.
  - **Default**: `meta-llama/Llama-3.1-3B-Instruct`
- **`GROQ_AI_MODEL`**
  - **Purpose**: Model ID on Groq for LLM meeting notes.
  - **Default**: `llama-3.3-70b-versatile`
- **`OLLAMA_BASE_URL`**
  - **Purpose**: URL for local Ollama server instance.
  - **Default**: `http://localhost:11434`
- **`OLLAMA_MODEL`**
  - **Purpose**: Local Ollama model tag.
  - **Default**: `llama3.1`
- **`GEMINI_API_KEY`**
  - **Purpose**: Google Gemini API key.
  - **Default**: `""`
  - **How to obtain**:
    1. Open [Google AI Studio](https://aistudio.google.com/app/apikey).
    2. Click **"Get API key"** and create a new key in a project.
    3. Copy the key and paste as `GEMINI_API_KEY`.
- **`GEMINI_MODEL`**
  - **Purpose**: Gemini model identifier.
  - **Default**: `gemini-2.0-flash`

### 5. Server & Host Configuration
- **`HOST`**
  - **Purpose**: Host address for application binding (`0.0.0.0` for containers/production).
  - **Default**: `0.0.0.0`
- **`PORT`**
  - **Purpose**: Service HTTP port.
  - **Default**: `3000`
- **`CORS_ORIGINS`**
  - **Purpose**: Allowed CORS origins JSON array or comma-separated list.
  - **Default**: `["http://localhost:3000","http://localhost:5173"]`
- **`LOG_LEVEL`**
  - **Purpose**: Logging severity level (`info`, `debug`, `warning`, `error`).
  - **Default**: `info`
