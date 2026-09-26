"""Session file manager — maintains durable raw transcript text files and AI artifact documents per meeting."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

DOCS_BASE_DIR = Path("./meeting_docs")


class SessionFileManager:
    """Manages raw transcript files and AI artifact documents per meeting session."""

    def __init__(self, base_dir: Path = DOCS_BASE_DIR):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def get_meeting_dir(self, meeting_id: str) -> Path:
        """Get or create directory for a meeting's session documents."""
        meeting_dir = self.base_dir / meeting_id
        meeting_dir.mkdir(parents=True, exist_ok=True)
        return meeting_dir

    def get_raw_transcript_path(self, meeting_id: str) -> Path:
        """Path to the raw session transcript file."""
        return self.get_meeting_dir(meeting_id) / "raw_transcript.txt"

    def append_segment(
        self,
        meeting_id: str,
        start_time: float,
        end_time: float,
        text: str,
        segment_index: int,
    ) -> str:
        """Append a processed 1-minute segment to the session's raw transcript file.

        Returns the formatted segment line.
        """
        raw_file = self.get_raw_transcript_path(meeting_id)
        ts_start = self._format_timestamp(start_time)
        ts_end = self._format_timestamp(end_time)
        line = f"[{ts_start} - {ts_end}] Segment #{segment_index + 1}: {text.strip()}\n"

        with open(raw_file, "a", encoding="utf-8") as f:
            f.write(line)

        logger.debug("Appended segment %d to session file %s", segment_index, raw_file)
        return line

    def read_raw_transcript(self, meeting_id: str) -> str:
        """Read the complete raw transcript file for a session."""
        raw_file = self.get_raw_transcript_path(meeting_id)
        if not raw_file.exists():
            return ""
        with open(raw_file, "r", encoding="utf-8") as f:
            return f.read()

    def save_artifact_file(
        self,
        meeting_id: str,
        artifact_type: str,  # e.g., 'minutes', 'highlights', 'action_items', 'proposals'
        content: str,
    ) -> Path:
        """Save an AI-generated artifact file (e.g. minutes_of_meeting.md)."""
        meeting_dir = self.get_meeting_dir(meeting_id)
        filename = f"{artifact_type}.md"
        file_path = meeting_dir / filename

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info("Saved AI artifact '%s' for meeting %s to %s", artifact_type, meeting_id, file_path)
        return file_path

    def list_artifacts(self, meeting_id: str) -> Dict[str, str]:
        """List all generated artifact files for a meeting session."""
        meeting_dir = self.get_meeting_dir(meeting_id)
        if not meeting_dir.exists():
            return {}

        artifacts = {}
        for file_path in meeting_dir.glob("*.md"):
            artifact_type = file_path.stem
            with open(file_path, "r", encoding="utf-8") as f:
                artifacts[artifact_type] = f.read()
        return artifacts

    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"


# Singleton instance
session_file_manager = SessionFileManager()
