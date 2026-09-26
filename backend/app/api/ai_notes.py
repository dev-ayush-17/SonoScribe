"""AI notes API endpoints — windowed generation and multi-artifact document serving."""

from __future__ import annotations

import json
import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import get_db
from app.models import AiNote, Meeting
from app.schemas import ActionItem, AiNoteRequest, AiNoteResponse
from app.services.ai.notes import create_ai_provider, generate_windowed_meeting_artifacts
from app.services.session_files import session_file_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/meetings", tags=["ai-notes"])


def _parse_json_field(value):
    if not value:
        return None
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return None


def _note_to_response(note: AiNote) -> AiNoteResponse:
    action_items_raw = _parse_json_field(note.action_items)
    action_items = None
    if action_items_raw:
        action_items = []
        for item in action_items_raw:
            if isinstance(item, dict):
                action_items.append(ActionItem(
                    task=item.get("task", str(item)),
                    owner=item.get("owner", "unspecified"),
                    due_date=item.get("due_date", "unspecified"),
                ))
            else:
                action_items.append(ActionItem(task=str(item)))

    return AiNoteResponse(
        id=note.id,
        meeting_id=note.meeting_id,
        provider=note.provider,
        model=note.model,
        summary=note.summary,
        decisions=_parse_json_field(note.decisions),
        action_items=action_items,
        open_questions=_parse_json_field(note.open_questions),
        notable_timestamps=_parse_json_field(note.notable_timestamps),
        status=note.status,
        error_message=note.error_message,
        created_at=note.created_at,
    )


@router.post("/{meeting_id}/ai-notes", response_model=dict)
async def generate_ai_notes(
    meeting_id: str,
    request: AiNoteRequest = AiNoteRequest(),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Generate windowed AI notes (minutes, highlights, proposals, action items) for a meeting."""
    # Read raw transcript file
    raw_transcript = session_file_manager.read_raw_transcript(meeting_id)

    # Fallback to DB segments if file not found
    if not raw_transcript:
        query = (
            select(Meeting)
            .options(selectinload(Meeting.segments))
            .where(Meeting.id == meeting_id)
        )
        result = await db.execute(query)
        meeting = result.scalar_one_or_none()
        if not meeting or not meeting.segments:
            raise HTTPException(status_code=400, detail="No transcript available for this meeting")

        segments = sorted(meeting.segments, key=lambda s: s.segment_index)
        raw_transcript = "\n".join([f"[{seg.start_time:.1f}s] {seg.text}" for seg in segments])

    provider_name = request.provider or settings.ai_provider
    if provider_name == "none":
        raise HTTPException(
            status_code=400,
            detail="No AI provider configured. Set AI_PROVIDER in .env (huggingface, groq, ollama, or gemini)",
        )

    provider = create_ai_provider(provider_name=provider_name, model=request.model or "")
    if provider is None or not provider.is_available:
        raise HTTPException(
            status_code=400,
            detail=f"AI provider '{provider_name}' is not available. Check configuration/API keys.",
        )

    try:
        # Generate multi-artifact docs in 20-25m windows
        artifacts = await generate_windowed_meeting_artifacts(
            meeting_id=meeting_id,
            transcript_text=raw_transcript,
            provider_name=provider_name,
        )

        # Save record in DB
        ai_note = AiNote(
            meeting_id=meeting_id,
            provider=provider_name,
            model=request.model or getattr(provider, "_model", ""),
            summary=artifacts.get("minutes_of_meeting", ""),
            decisions=json.dumps([artifacts.get("highlights", "")]),
            action_items=json.dumps([artifacts.get("action_items", "")]),
            open_questions=json.dumps([artifacts.get("proposals_and_future_plans", "")]),
            status="completed",
        )
        db.add(ai_note)
        await db.commit()

        logger.info("AI windowed artifacts generated for meeting %s via %s", meeting_id, provider_name)
        return {
            "status": "completed",
            "meeting_id": meeting_id,
            "provider": provider_name,
            "artifacts": artifacts,
            "note": _note_to_response(ai_note),
        }

    except Exception as e:
        logger.error("AI notes generation failed: %s", e)
        raise HTTPException(status_code=500, detail=f"AI notes generation failed: {e}")


@router.get("/{meeting_id}/artifacts")
async def list_meeting_artifacts(meeting_id: str) -> dict:
    """Get all saved session artifact files (raw transcript, minutes, highlights, action items, proposals)."""
    raw_transcript = session_file_manager.read_raw_transcript(meeting_id)
    artifacts = session_file_manager.list_artifacts(meeting_id)

    return {
        "meeting_id": meeting_id,
        "raw_transcript": raw_transcript,
        "artifacts": artifacts,
    }
