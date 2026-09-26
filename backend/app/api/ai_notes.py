"""AI notes API endpoints."""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import get_db
from app.models import AiNote, Meeting, TranscriptSegment
from app.schemas import AiNoteRequest, AiNoteResponse, ActionItem
from app.services.ai.notes import create_ai_provider

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


def _format_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


@router.post("/{meeting_id}/ai-notes", response_model=AiNoteResponse)
async def generate_ai_notes(
    meeting_id: str,
    request: AiNoteRequest = AiNoteRequest(),
    db: AsyncSession = Depends(get_db),
) -> AiNoteResponse:
    """Generate AI notes for a meeting. Requires configured AI provider."""
    # Get meeting with segments
    query = (
        select(Meeting)
        .options(selectinload(Meeting.segments))
        .where(Meeting.id == meeting_id)
    )
    result = await db.execute(query)
    meeting = result.scalar_one_or_none()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if not meeting.segments:
        raise HTTPException(status_code=400, detail="No transcript segments found for this meeting")

    # Determine provider
    provider_name = request.provider or settings.ai_provider
    if provider_name == "none":
        raise HTTPException(
            status_code=400,
            detail="No AI provider configured. Set AI_PROVIDER in .env (groq, ollama, or gemini)",
        )

    try:
        provider = create_ai_provider(
            provider_name=provider_name,
            model=request.model or "",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if provider is None or not provider.is_available:
        raise HTTPException(
            status_code=400,
            detail=f"AI provider '{provider_name}' is not available. Check configuration/API keys.",
        )

    # Create pending note
    ai_note = AiNote(
        meeting_id=meeting_id,
        provider=provider_name,
        model=request.model or getattr(provider, '_model', ''),
        status="processing",
    )
    db.add(ai_note)
    await db.flush()

    # Build transcript text
    segments = sorted(meeting.segments, key=lambda s: s.segment_index)
    transcript_lines = []
    for seg in segments:
        ts = _format_timestamp(seg.start_time)
        transcript_lines.append(f"[{ts}] {seg.text}")
    transcript_text = "\n".join(transcript_lines)

    try:
        # Generate notes
        notes = await provider.generate_for_long_transcript(transcript_text)

        # Update the note record
        ai_note.summary = notes.get("summary", "")
        ai_note.decisions = json.dumps(notes.get("decisions", []))
        ai_note.action_items = json.dumps(notes.get("action_items", []))
        ai_note.open_questions = json.dumps(notes.get("open_questions", []))
        ai_note.notable_timestamps = json.dumps(notes.get("notable_timestamps", []))
        ai_note.raw_response = json.dumps(notes)
        ai_note.status = "completed"

        await db.flush()

        logger.info("AI notes generated for meeting %s via %s", meeting_id, provider_name)
        return _note_to_response(ai_note)

    except Exception as e:
        logger.error("AI notes generation failed: %s", e)
        ai_note.status = "failed"
        ai_note.error_message = str(e)
        await db.flush()
        raise HTTPException(
            status_code=500,
            detail=f"AI notes generation failed: {e}",
        )


@router.get("/{meeting_id}/ai-notes", response_model=list)
async def list_ai_notes(
    meeting_id: str,
    db: AsyncSession = Depends(get_db),
) -> list:
    """List all AI notes for a meeting."""
    query = select(AiNote).where(AiNote.meeting_id == meeting_id).order_by(AiNote.created_at.desc())
    result = await db.execute(query)
    notes = result.scalars().all()
    return [_note_to_response(note) for note in notes]
