"""AI notes service — generates summaries, decisions, action items, and multi-artifact documents using 20-25 min windowed blocks."""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from app.config import settings
from app.services.session_files import session_file_manager

logger = logging.getLogger(__name__)

# System prompt for windowed meeting notes extraction
NOTES_SYSTEM_PROMPT = """You are an expert meeting notes assistant. Analyze the meeting transcript portion and extract clear, actionable insights.

IMPORTANT RULES:
1. Only include facts explicitly stated in the transcript.
2. Clearly distinguish between explicit facts and inferences/assumptions.
3. If information is ambiguous, put it in "open_questions".
4. For action items, identify the owner and due date if stated (use "unspecified" if not).
5. Extract proposals, future plans, schedules, and key meeting highlights.

Return valid JSON with exactly these fields:
{
  "summary": "A concise 2-4 paragraph executive summary",
  "highlights": ["Key point or major topic discussed"],
  "decisions": ["Explicit decisions agreed upon"],
  "action_items": [
    {"task": "Action item description", "owner": "Person responsible or 'unspecified'", "due_date": "Due date or 'unspecified'"}
  ],
  "proposals_and_future_plans": ["Proposals, strategy ideas, or future roadmap items discussed"],
  "schedules_and_milestones": ["Deadlines, release dates, or scheduled events"],
  "open_questions": ["Unresolved questions or assumptions"],
  "notable_timestamps": ["HH:MM:SS - Significant event or decision"]
}"""

WINDOW_EXTRACTION_PROMPT = """Analyze this 20-25 minute section of the meeting transcript:

{text}

Extract key highlights, decisions, action items, proposals, and schedules according to the format."""


class AiNotesProvider(ABC):
    """Abstract base class for AI notes providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def is_available(self) -> bool:
        ...

    @abstractmethod
    async def generate(self, transcript_text: str) -> dict:
        """Generate notes from transcript text."""
        ...

    async def generate_windowed_artifacts(
        self,
        transcript_text: str,
        window_minutes: int = 25,
    ) -> Dict[str, str]:
        """Process transcript in 20-25 minute windowed blocks rather than entire file at once.

        Returns dict of artifact filename -> markdown content.
        """
        lines = transcript_text.strip().split("\n")
        if not lines or not lines[0]:
            return {}

        # Split transcript lines into ~20-25 minute windows
        # 1 minute per chunk -> 20-25 lines per window
        lines_per_window = window_minutes
        windows = [lines[i:i + lines_per_window] for i in range(0, len(lines), lines_per_window)]

        logger.info("Processing transcript in %d windowed blocks (%d mins each)", len(windows), window_minutes)

        window_results = []
        for idx, window_lines in enumerate(windows):
            window_text = "\n".join(window_lines)
            start_min = idx * window_minutes
            end_min = (idx + 1) * window_minutes
            logger.info("Processing AI window #%d (%d min - %d min)...", idx + 1, start_min, end_min)

            try:
                result = await self.generate(window_text)
                window_results.append(result)
            except Exception as e:
                logger.warning("Error processing AI window #%d: %s", idx + 1, e)

        # Synthesize window results into multi-artifact documents
        return _synthesize_multi_artifacts(window_results)


def _parse_ai_response(response_text: str) -> dict:
    """Parse AI response text into structured dict safely."""
    text = response_text.strip()
    import re

    # Direct JSON parse
    try:
        return _validate_notes(json.loads(text))
    except json.JSONDecodeError:
        pass

    # Markdown block
    json_match = re.search(r"```(?:json)?\s*\n(.*?)\n```", text, re.DOTALL)
    if json_match:
        try:
            return _validate_notes(json.loads(json_match.group(1)))
        except json.JSONDecodeError:
            pass

    # Find JSON object
    b_start = text.find("{")
    b_end = text.rfind("}")
    if b_start != -1 and b_end != -1:
        try:
            return _validate_notes(json.loads(text[b_start:b_end + 1]))
        except json.JSONDecodeError:
            pass

    return {
        "summary": text,
        "highlights": [],
        "decisions": [],
        "action_items": [],
        "proposals_and_future_plans": [],
        "schedules_and_milestones": [],
        "open_questions": [],
        "notable_timestamps": [],
    }


def _validate_notes(data: dict) -> dict:
    """Validate notes dictionary structure."""
    return {
        "summary": data.get("summary", ""),
        "highlights": data.get("highlights", []) if isinstance(data.get("highlights"), list) else [],
        "decisions": data.get("decisions", []) if isinstance(data.get("decisions"), list) else [],
        "action_items": _validate_action_items(data.get("action_items", [])),
        "proposals_and_future_plans": data.get("proposals_and_future_plans", []) if isinstance(data.get("proposals_and_future_plans"), list) else [],
        "schedules_and_milestones": data.get("schedules_and_milestones", []) if isinstance(data.get("schedules_and_milestones"), list) else [],
        "open_questions": data.get("open_questions", []) if isinstance(data.get("open_questions"), list) else [],
        "notable_timestamps": data.get("notable_timestamps", []) if isinstance(data.get("notable_timestamps"), list) else [],
    }


def _validate_action_items(items) -> list:
    if not isinstance(items, list):
        return []
    res = []
    for item in items:
        if isinstance(item, dict):
            res.append({
                "task": item.get("task", str(item)),
                "owner": item.get("owner", "unspecified"),
                "due_date": item.get("due_date", "unspecified"),
            })
        elif isinstance(item, str):
            res.append({"task": item, "owner": "unspecified", "due_date": "unspecified"})
    return res


def _synthesize_multi_artifacts(results: List[dict]) -> Dict[str, str]:
    """Synthesize window results into multi-artifact markdown documents."""
    summaries = [r["summary"] for r in results if r.get("summary")]
    highlights = [h for r in results for h in r.get("highlights", [])]
    decisions = [d for r in results for d in r.get("decisions", [])]
    action_items = [a for r in results for a in r.get("action_items", [])]
    proposals = [p for r in results for p in r.get("proposals_and_future_plans", [])]
    schedules = [s for r in results for s in r.get("schedules_and_milestones", [])]
    questions = [q for r in results for q in r.get("open_questions", [])]

    # Minutes of Meeting
    minutes_lines = ["# Minutes of Meeting", "", "## Executive Summary", ""]
    minutes_lines.extend(summaries or ["No summary generated."])
    minutes_lines.extend(["", "## Key Decisions", ""])
    for d in (decisions or ["None explicitly stated."]):
        minutes_lines.append(f"- {d}")

    # Highlights
    highlights_lines = ["# Meeting Highlights & Key Points", ""]
    for h in (highlights or ["No specific highlights extracted."]):
        highlights_lines.append(f"- {h}")

    # Action Items & Schedules
    actions_lines = ["# Action Items, Owners & Schedules", "", "## Action Items", ""]
    for a in action_items:
        if isinstance(a, dict):
            actions_lines.append(f"- [ ] **{a.get('task')}** (Owner: {a.get('owner', 'unspecified')}, Due: {a.get('due_date', 'unspecified')})")
        else:
            actions_lines.append(f"- [ ] {a}")
    if not action_items:
        actions_lines.append("No action items assigned.")

    actions_lines.extend(["", "## Schedules & Milestones", ""])
    for s in (schedules or ["No deadlines mentioned."]):
        actions_lines.append(f"- {s}")

    # Proposals & Future Plans
    proposals_lines = ["# Proposals & Future Plans", ""]
    for p in (proposals or ["No future proposals recorded."]):
        proposals_lines.append(f"- {p}")

    if questions:
        proposals_lines.extend(["", "## Open Questions & Assumptions", ""])
        for q in questions:
            proposals_lines.append(f"- {q}")

    return {
        "minutes_of_meeting": "\n".join(minutes_lines),
        "highlights": "\n".join(highlights_lines),
        "action_items": "\n".join(actions_lines),
        "proposals_and_future_plans": "\n".join(proposals_lines),
    }


class GroqAiProvider(AiNotesProvider):
    """AI notes using Groq API."""

    def __init__(self, api_key: str, model: str = "llama-3.1-70b-versatile"):
        self._api_key = api_key
        self._model = model

    @property
    def name(self) -> str:
        return "groq"

    @property
    def is_available(self) -> bool:
        return bool(self._api_key)

    async def generate(self, transcript_text: str) -> dict:
        from groq import AsyncGroq
        client = AsyncGroq(api_key=self._api_key)
        response = await client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": NOTES_SYSTEM_PROMPT},
                {"role": "user", "content": WINDOW_EXTRACTION_PROMPT.format(text=transcript_text)},
            ],
            temperature=0.3,
            max_tokens=4096,
            response_format={"type": "json_object"},
        )
        return _parse_ai_response(response.choices[0].message.content)


class OllamaAiProvider(AiNotesProvider):
    """AI notes using local Ollama."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.1"):
        self._base_url = base_url
        self._model = model

    @property
    def name(self) -> str:
        return "ollama"

    @property
    def is_available(self) -> bool:
        return True

    async def generate(self, transcript_text: str) -> dict:
        import httpx
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self._base_url}/api/chat",
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": NOTES_SYSTEM_PROMPT},
                        {"role": "user", "content": WINDOW_EXTRACTION_PROMPT.format(text=transcript_text)},
                    ],
                    "stream": False,
                    "format": "json",
                },
            )
            response.raise_for_status()
            return _parse_ai_response(response.json()["message"]["content"])


class GeminiAiProvider(AiNotesProvider):
    """AI notes using Google Gemini."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self._api_key = api_key
        self._model = model

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def is_available(self) -> bool:
        return bool(self._api_key)

    async def generate(self, transcript_text: str) -> dict:
        from google import genai
        client = genai.Client(api_key=self._api_key)
        response = await client.aio.models.generate_content(
            model=self._model,
            contents=f"{NOTES_SYSTEM_PROMPT}\n\n{WINDOW_EXTRACTION_PROMPT.format(text=transcript_text)}",
        )
        return _parse_ai_response(response.text)


def create_ai_provider(
    provider_name: str = "",
    api_key: str = "",
    model: str = "",
    base_url: str = "",
) -> Optional[AiNotesProvider]:
    """Factory function to create an AI notes provider."""
    p_name = provider_name or settings.ai_provider
    if p_name == "groq":
        return GroqAiProvider(
            api_key=api_key or settings.groq_api_key,
            model=model or settings.groq_ai_model,
        )
    elif p_name == "ollama":
        return OllamaAiProvider(
            base_url=base_url or settings.ollama_base_url,
            model=model or settings.ollama_model,
        )
    elif p_name == "gemini":
        return GeminiAiProvider(
            api_key=api_key or settings.gemini_api_key,
            model=model or settings.gemini_model,
        )
    elif p_name == "none" or not p_name:
        return None
    else:
        raise ValueError(f"Unknown AI provider: {p_name}")


async def generate_windowed_meeting_artifacts(
    meeting_id: str,
    transcript_text: str,
    provider_name: str = "",
) -> Dict[str, str]:
    """Generate multi-artifact markdown files using 20-25 minute windowed AI processing."""
    provider = create_ai_provider(provider_name)
    if provider is None or not provider.is_available:
        logger.warning("No available AI provider for meeting %s", meeting_id)
        return {}

    artifacts = await provider.generate_windowed_artifacts(transcript_text, window_minutes=25)

    # Save each generated artifact to disk via SessionFileManager
    for artifact_name, content in artifacts.items():
        session_file_manager.save_artifact_file(meeting_id, artifact_name, content)

    return artifacts
