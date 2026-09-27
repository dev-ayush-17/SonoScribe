# ── Stage 1: Build Frontend ──
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# ── Stage 2: Build Backend & Production Runner ──
FROM python:3.12-slim AS runner
WORKDIR /app

# Install system dependencies (PortAudio & ffmpeg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    portaudio19-dev \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy backend source code
COPY backend/ ./backend/

# Copy built frontend assets to app mount
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Environment defaults
ENV HOST=0.0.0.0
ENV PORT=3000
ENV PYTHONPATH=/app/backend

EXPOSE 3000
EXPOSE 8000

WORKDIR /app/backend

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3000"]
