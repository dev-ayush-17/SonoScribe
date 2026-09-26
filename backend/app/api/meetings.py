"""Meetings CRUD API endpoints."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Meeting, TranscriptSegment, AiNote
from app.schemas import (
    MeetingCreate,
    MeetingDetail,
    MeetingResponse,
    MeetingUpdate,
    TranscriptSegmentResponse,
    AiNoteResponse,
    ActionItem,
    ExportRequest,
)

router = APIRouter(prefix="/meetings", tags=["meetings"])


def _meeting_to_response(meeting: Meeting, segment_count: int = 0) -> MeetingResponse:
    """Convert a Meeting model to a MeetingResponse."""
    return MeetingResponse(
        id=meeting.id,
        title=meeting.title,
        started_at=meeting.started_at,
        ended_at=meeting.ended_at,
        duration_seconds=meeting.duration_seconds,
        status=meeting.status,
        audio_device=meeting.audio_device,
        sample_rate=meeting.sample_rate,
        segment_count=segment_count,
        created_at=meeting.created_at,
        updated_at=meeting.updated_at,
    )


def _parse_json_field(value: Optional[str]) -> Optional[list]:
    """Safely parse a JSON string field."""
    if not value:
        return None
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return None


def _note_to_response(note: AiNote) -> AiNoteResponse:
    """Convert an AiNote model to a response."""
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


@router.get("", response_model=List[MeetingResponse])
async def list_meetings(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> List[MeetingResponse]:
    """List all meetings, newest first."""
    query = select(Meeting).order_by(Meeting.started_at.desc())
    if status:
        query = query.where(Meeting.status == status)
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    meetings = result.scalars().all()

    # Get segment counts
    responses = []
    for meeting in meetings:
        count_q = select(func.count()).where(
            TranscriptSegment.meeting_id == meeting.id
        )
        count_result = await db.execute(count_q)
        count = count_result.scalar() or 0
        responses.append(_meeting_to_response(meeting, count))

    return responses


@router.get("/{meeting_id}", response_model=MeetingDetail)
async def get_meeting(
    meeting_id: str,
    db: AsyncSession = Depends(get_db),
) -> MeetingDetail:
    """Get a meeting with its transcript segments and AI notes."""
    query = (
        select(Meeting)
        .options(selectinload(Meeting.segments), selectinload(Meeting.ai_notes))
        .where(Meeting.id == meeting_id)
    )
    result = await db.execute(query)
    meeting = result.scalar_one_or_none()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    segments = [
        TranscriptSegmentResponse.model_validate(seg)
        for seg in meeting.segments
    ]
    notes = [_note_to_response(note) for note in meeting.ai_notes]

    return MeetingDetail(
        id=meeting.id,
        title=meeting.title,
        started_at=meeting.started_at,
        ended_at=meeting.ended_at,
        duration_seconds=meeting.duration_seconds,
        status=meeting.status,
        audio_device=meeting.audio_device,
        sample_rate=meeting.sample_rate,
        segment_count=len(segments),
        created_at=meeting.created_at,
        updated_at=meeting.updated_at,
        segments=segments,
        ai_notes=notes,
    )


@router.patch("/{meeting_id}", response_model=MeetingResponse)
async def update_meeting(
    meeting_id: str,
    update: MeetingUpdate,
    db: AsyncSession = Depends(get_db),
) -> MeetingResponse:
    """Update a meeting's title or status."""
    query = select(Meeting).where(Meeting.id == meeting_id)
    result = await db.execute(query)
    meeting = result.scalar_one_or_none()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if update.title is not None:
        meeting.title = update.title
    if update.status is not None:
        meeting.status = update.status
    meeting.updated_at = datetime.now(timezone.utc)

    await db.commit()
    return _meeting_to_response(meeting)


@router.delete("/{meeting_id}")
async def delete_meeting(
    meeting_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete a meeting and all its segments and notes."""
    query = select(Meeting).where(Meeting.id == meeting_id)
    result = await db.execute(query)
    meeting = result.scalar_one_or_none()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    await db.delete(meeting)
    await db.commit()
    return {"detail": "Meeting deleted"}


@router.get("/{meeting_id}/export")
async def export_transcript(
    meeting_id: str,
    format: str = Query("markdown", pattern="^(markdown|text|json)$"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Export a meeting's transcript in the specified format."""
    query = (
        select(Meeting)
        .options(selectinload(Meeting.segments), selectinload(Meeting.ai_notes))
        .where(Meeting.id == meeting_id)
    )
    result = await db.execute(query)
    meeting = result.scalar_one_or_none()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    segments = sorted(meeting.segments, key=lambda s: s.segment_index)

    if format == "markdown":
        content = _export_markdown(meeting, segments, meeting.ai_notes)
    elif format == "text":
        content = _export_text(meeting, segments)
    else:
        content = _export_json(meeting, segments, meeting.ai_notes)

    return {"content": content, "format": format, "meeting_id": meeting_id}


def _format_timestamp(seconds: float) -> str:
    """Format seconds as HH:MM:SS."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def _export_markdown(
    meeting: Meeting,
    segments: list,
    notes: list,
) -> str:
    """Export as Markdown."""
    lines = [
        f"# {meeting.title}",
        "",
        f"**Date**: {meeting.started_at.strftime('%Y-%m-%d %H:%M')}",
        f"**Duration**: {_format_timestamp(meeting.duration_seconds or 0)}",
        f"**Status**: {meeting.status}",
        "",
    ]

    # AI notes if available
    completed_notes = [n for n in notes if n.status == "completed"]
    if completed_notes:
        note = completed_notes[-1]
        if note.summary:
            lines.extend(["## Summary", "", note.summary, ""])
        decisions = _parse_json_field(note.decisions)
        if decisions:
            lines.extend(["## Decisions", ""])
            for d in decisions:
                lines.append(f"- {d}")
            lines.append("")
        action_items = _parse_json_field(note.action_items)
        if action_items:
            lines.extend(["## Action Items", ""])
            for item in action_items:
                if isinstance(item, dict):
                    owner = item.get("owner", "unspecified")
                    due = item.get("due_date", "unspecified")
                    lines.append(f"- [ ] {item.get('task', item)} (Owner: {owner}, Due: {due})")
                else:
                    lines.append(f"- [ ] {item}")
            lines.append("")
        open_q = _parse_json_field(note.open_questions)
        if open_q:
            lines.extend(["## Open Questions", ""])
            for q in open_q:
                lines.append(f"- {q}")
            lines.append("")

    # Transcript
    lines.extend(["## Transcript", ""])
    for seg in segments:
        ts = _format_timestamp(seg.start_time)
        lines.append(f"**[{ts}]** {seg.text}")
        lines.append("")

    return "\n".join(lines)


def _export_text(meeting: Meeting, segments: list) -> str:
    """Export as plain text."""
    lines = [
        meeting.title,
        f"Date: {meeting.started_at.strftime('%Y-%m-%d %H:%M')}",
        f"Duration: {_format_timestamp(meeting.duration_seconds or 0)}",
        "",
        "--- Transcript ---",
        "",
    ]
    for seg in segments:
        ts = _format_timestamp(seg.start_time)
        lines.append(f"[{ts}] {seg.text}")
    return "\n".join(lines)


def _export_json(meeting: Meeting, segments: list, notes: list) -> str:
    """Export as JSON string."""
    import json as json_mod

    data = {
        "meeting": {
            "id": meeting.id,
            "title": meeting.title,
            "started_at": meeting.started_at.isoformat(),
            "ended_at": meeting.ended_at.isoformat() if meeting.ended_at else None,
            "duration_seconds": meeting.duration_seconds,
            "status": meeting.status,
        },
        "segments": [
            {
                "index": seg.segment_index,
                "start_time": seg.start_time,
                "end_time": seg.end_time,
                "text": seg.text,
                "confidence": seg.confidence,
                "provider": seg.provider,
            }
            for seg in segments
        ],
    }
    completed_notes = [n for n in notes if n.status == "completed"]
    if completed_notes:
        note = completed_notes[-1]
        data["ai_notes"] = {
            "summary": note.summary,
            "decisions": _parse_json_field(note.decisions),
            "action_items": _parse_json_field(note.action_items),
            "open_questions": _parse_json_field(note.open_questions),
        }
    return json_mod.dumps(data, indent=2)
