"""SonoScribe FastAPI Application Entry Point."""

from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.api.ai_notes import router as ai_notes_router
from app.api.health import router as health_router
from app.api.meetings import router as meetings_router
from app.api.recording import router as recording_router
from app.config import settings
from app.database import close_db, init_db
from app.services.recording import recording_manager

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("sonoscribe")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("Starting SonoScribe backend...")
    await init_db()
    yield
    logger.info("Shutting down SonoScribe backend...")
    await close_db()


app = FastAPI(
    title="SonoScribe API",
    description="Local-first meeting recorder and transcription service API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(health_router, prefix="/api/v1")
app.include_router(meetings_router, prefix="/api/v1")
app.include_router(recording_router, prefix="/api/v1")
app.include_router(ai_notes_router, prefix="/api/v1")

# Mount built frontend static files if available
from pathlib import Path
from fastapi.staticfiles import StaticFiles

dist_candidates = [Path("../frontend/dist"), Path("./frontend/dist"), Path("/app/frontend/dist")]
for dist_path in dist_candidates:
    if dist_path.exists():
        logger.info("Mounting frontend static dist from %s", dist_path.resolve())
        app.mount("/", StaticFiles(directory=str(dist_path.resolve()), html=True), name="static")
        break



# Active WebSocket connection manager for live transcript streaming
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning("Error sending websocket message: %s", e)
                self.disconnect(connection)


ws_manager = ConnectionManager()


@app.websocket("/ws/transcript")
async def websocket_transcript_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time transcript segment streaming and recording state updates."""
    await ws_manager.connect(websocket)
    try:
        # Send initial status
        await websocket.send_json({
            "type": "status",
            "data": recording_manager.get_status(),
        })
        while True:
            # Keep connection alive and receive ping/messages if any
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.warning("WebSocket error: %s", e)
        ws_manager.disconnect(websocket)


# Hook recording manager segment callback to broadcast over websocket
async def _on_segment_callback(segment_data: dict):
    await ws_manager.broadcast({
        "type": "segment",
        "data": segment_data,
    })

# Register callback
recording_manager._on_segment = _on_segment_callback


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
