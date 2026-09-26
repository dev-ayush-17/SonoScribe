"""AI notes service — generates summaries, decisions, action items from transcripts."""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)

# Prompt template for AI notes generation
NOTES_SYSTEM_PROMPT = """You are a meeting notes assistant. Analyze the meeting transcript and produce structured notes.

IMPORTANT RULES:
1. Only include information explicitly stated in the transcript.
2. Clearly distinguish between explicit facts and your inferences/assumptions.
3. If information is unclear or ambiguous, note it in "open_questions".
4. For action items, extract the owner and due date if mentioned. Use "unspecified" if not stated.
5. Include notable timestamps when significant topics or decisions are discussed.

Return your response as valid JSON with exactly these fields:
{
  "summary": "A concise 2-4 paragraph summary of the meeting",
  "decisions": ["List of explicit decisions made during the meeting"],
  "action_items": [
    {"task": "Description of the action item", "owner": "Person responsible or 'unspecified'", "due_date": "Due date or 'unspecified'"}
  ],
  "open_questions": ["Questions that were raised but not resolved"],
  "notable_timestamps": ["HH:MM:SS - Brief description of what happened at this time"]
}

If the transcript is very short or has no meaningful content, still return the JSON structure with empty arrays and a brief summary noting the lack of content."""

CHUNK_SUMMARY_PROMPT = """Summarize this portion of a meeting transcript concisely, preserving:
- Key decisions made
- Action items assigned (with owners/dates if mentioned)
- Important topics discussed
- Any open questions

Transcript portion:
{text}

Provide a concise summary:"""

SYNTHESIS_PROMPT = """You have summaries of different portions of a meeting. Synthesize them into a complete set of meeting notes.

Chunk summaries:
{summaries}

""" + NOTES_SYSTEM_PROMPT


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
        """Generate notes from transcript text.

        Returns dict with: summary, decisions, action_items, open_questions, notable_timestamps
        """
        ...

    async def generate_for_long_transcript(
        self,
        transcript_text: str,
        max_chunk_chars: int = 8000,
    ) -> dict:
        """Handle long transcripts by summarizing chunks then synthesizing."""
        if len(transcript_text) <= max_chunk_chars:
            return await self.generate(transcript_text)

        # Split into chunks
        chunks = []
        lines = transcript_text.split("\n")
        current_chunk = []
        current_len = 0
        for line in lines:
            if current_len + len(line) > max_chunk_chars and current_chunk:
                chunks.append("\n".join(current_chunk))
                current_chunk = [line]
                current_len = len(line)
            else:
                current_chunk.append(line)
                current_len += len(line)
        if current_chunk:
            chunks.append("\n".join(current_chunk))

        logger.info("Splitting transcript into %d chunks for summarization", len(chunks))

        # Summarize each chunk
        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            try:
                summary = await self._summarize_chunk(chunk)
                chunk_summaries.append(f"--- Part {i+1} ---\n{summary}")
            except Exception as e:
                logger.warning("Failed to summarize chunk %d: %s", i, e)
                chunk_summaries.append(f"--- Part {i+1} ---\n[Summarization failed: {e}]")

        # Synthesize
        combined_summaries = "\n\n".join(chunk_summaries)
        return await self._synthesize(combined_summaries)

    @abstractmethod
    async def _summarize_chunk(self, chunk_text: str) -> str:
        """Summarize a single chunk of transcript."""
        ...

    @abstractmethod
    async def _synthesize(self, summaries_text: str) -> dict:
        """Synthesize chunk summaries into final notes."""
        ...


def _parse_ai_response(response_text: str) -> dict:
    """Parse AI response text into structured notes dict.

    Handles malformed JSON gracefully.
    """
    # Try to extract JSON from response
    text = response_text.strip()

    # Try direct parse
    try:
        data = json.loads(text)
        return _validate_notes(data)
    except json.JSONDecodeError:
        pass

    # Try to find JSON block in markdown code fences
    import re
    json_match = re.search(r"```(?:json)?\s*\n(.*?)\n```", text, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group(1))
            return _validate_notes(data)
        except json.JSONDecodeError:
            pass

    # Try to find JSON object in text
    brace_start = text.find("{")
    brace_end = text.rfind("}")
    if brace_start != -1 and brace_end != -1:
        try:
            data = json.loads(text[brace_start:brace_end + 1])
            return _validate_notes(data)
        except json.JSONDecodeError:
            pass

    # Fallback: return raw text as summary
    logger.warning("Could not parse AI response as JSON, using raw text as summary")
    return {
        "summary": text,
        "decisions": [],
        "action_items": [],
        "open_questions": ["AI response could not be parsed into structured format"],
        "notable_timestamps": [],
    }


def _validate_notes(data: dict) -> dict:
    """Validate and normalize notes structure."""
    return {
        "summary": data.get("summary", ""),
        "decisions": data.get("decisions", []) if isinstance(data.get("decisions"), list) else [],
        "action_items": _validate_action_items(data.get("action_items", [])),
        "open_questions": data.get("open_questions", []) if isinstance(data.get("open_questions"), list) else [],
        "notable_timestamps": data.get("notable_timestamps", []) if isinstance(data.get("notable_timestamps"), list) else [],
    }


def _validate_action_items(items) -> list:
    """Validate action items format."""
    if not isinstance(items, list):
        return []
    result = []
    for item in items:
        if isinstance(item, dict):
            result.append({
                "task": item.get("task", str(item)),
                "owner": item.get("owner", "unspecified"),
                "due_date": item.get("due_date", "unspecified"),
            })
        elif isinstance(item, str):
            result.append({"task": item, "owner": "unspecified", "due_date": "unspecified"})
    return result


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
                {"role": "user", "content": f"Here is the meeting transcript:\n\n{transcript_text}"},
            ],
            temperature=0.3,
            max_tokens=4096,
            response_format={"type": "json_object"},
        )
        return _parse_ai_response(response.choices[0].message.content)

    async def _summarize_chunk(self, chunk_text: str) -> str:
        from groq import AsyncGroq

        client = AsyncGroq(api_key=self._api_key)
        response = await client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "user", "content": CHUNK_SUMMARY_PROMPT.format(text=chunk_text)},
            ],
            temperature=0.3,
            max_tokens=1024,
        )
        return response.choices[0].message.content

    async def _synthesize(self, summaries_text: str) -> dict:
        from groq import AsyncGroq

        client = AsyncGroq(api_key=self._api_key)
        response = await client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": NOTES_SYSTEM_PROMPT},
                {"role": "user", "content": SYNTHESIS_PROMPT.format(summaries=summaries_text)},
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
        return True  # Assume available if configured

    async def generate(self, transcript_text: str) -> dict:
        import httpx

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self._base_url}/api/chat",
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": NOTES_SYSTEM_PROMPT},
                        {"role": "user", "content": f"Meeting transcript:\n\n{transcript_text}"},
                    ],
                    "stream": False,
                    "format": "json",
                },
            )
            response.raise_for_status()
            data = response.json()
            return _parse_ai_response(data["message"]["content"])

    async def _summarize_chunk(self, chunk_text: str) -> str:
        import httpx

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self._base_url}/api/chat",
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "user", "content": CHUNK_SUMMARY_PROMPT.format(text=chunk_text)},
                    ],
                    "stream": False,
                },
            )
            response.raise_for_status()
            return response.json()["message"]["content"]

    async def _synthesize(self, summaries_text: str) -> dict:
        return await self.generate(summaries_text)


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
            contents=f"{NOTES_SYSTEM_PROMPT}\n\nMeeting transcript:\n\n{transcript_text}",
        )
        return _parse_ai_response(response.text)

    async def _summarize_chunk(self, chunk_text: str) -> str:
        from google import genai

        client = genai.Client(api_key=self._api_key)
        response = await client.aio.models.generate_content(
            model=self._model,
            contents=CHUNK_SUMMARY_PROMPT.format(text=chunk_text),
        )
        return response.text

    async def _synthesize(self, summaries_text: str) -> dict:
        return await self.generate(summaries_text)


def create_ai_provider(
    provider_name: str = "",
    api_key: str = "",
    model: str = "",
    base_url: str = "",
) -> Optional[AiNotesProvider]:
    """Factory function to create an AI notes provider."""
    if provider_name == "groq":
        return GroqAiProvider(
            api_key=api_key or settings.groq_api_key,
            model=model or settings.groq_ai_model,
        )
    elif provider_name == "ollama":
        return OllamaAiProvider(
            base_url=base_url or settings.ollama_base_url,
            model=model or settings.ollama_model,
        )
    elif provider_name == "gemini":
        return GeminiAiProvider(
            api_key=api_key or settings.gemini_api_key,
            model=model or settings.gemini_model,
        )
    elif provider_name == "none" or not provider_name:
        return None
    else:
        raise ValueError(f"Unknown AI provider: {provider_name}")
