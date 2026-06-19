"""Resume parsing service — fetches a PDF, extracts text, and structures it with Gemini.

Parsed data is cached in-process for 24 hours to avoid redundant PDF fetches and LLM calls.
Call clear_resume_cache() to force a re-parse on the next request.
"""
import asyncio
import io
import json
import re
import time
from typing import Any

import httpx
import pdfplumber
from google import genai
from google.genai import types

from src.config.log_config import setup_logging
from src.config.settings import GEMINI_MODEL, GOOGLE_API_KEY, RESUME_URL

logger = setup_logging(filename=__file__)

_CACHE_TTL: int = 24 * 3600  # seconds
_cache: dict[str, Any] = {"data": None, "ts": 0.0}

# Matches Google Drive file IDs in view/share/download URLs.
_GDRIVE_RE = re.compile(
    r"drive\.google\.com/(?:file/d/|open\?id=|uc\?.*id=)([A-Za-z0-9_-]+)"
)


def _normalise_url(url: str) -> str:
    """Convert a Google Drive view/share link to a direct-download URL."""
    m = _GDRIVE_RE.search(url)
    if m:
        file_id = m.group(1)
        return f"https://drive.google.com/uc?export=download&id={file_id}&confirm=t"
    return url


def _extract_text(pdf_bytes: bytes) -> str:
    """Extract plain text from all pages of a PDF, separated by double newlines."""
    pages: list[str] = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            text: str | None = page.extract_text()
            if text:
                pages.append(text)
    return "\n\n".join(pages)


def _parse_with_gemini(text: str) -> dict[str, Any]:
    """Send resume text to Gemini and return a structured JSON dict.

    Always produces an "about" string even when the resume has no summary section —
    Gemini synthesises one from experience, education, and skills.
    """
    client = genai.Client(api_key=GOOGLE_API_KEY)
    prompt = (
        "Extract structured data from this resume. "
        "Return a JSON object with exactly these top-level keys:\n\n"
        '- "about": string — ALWAYS required, never null. '
        "If the resume has a summary, profile, or objective section, rewrite it: "
        "keep every important detail but make it easy to read. "
        "Use plain, direct English — no buzzwords like 'passionate', 'results-driven', or 'dynamic'. "
        "Highlight what genuinely stands out (specific technologies, real numbers, unusual background). "
        "2–4 sentences maximum. "
        "If there is no summary section, write one from scratch using the experience, education, and skills you find — "
        "make it honest, specific, and something a recruiter would actually want to read.\n"
        '- "experience": array of objects, each with keys:\n'
        '    "jobTitle" (role/title), "company" (employer), '
        '"position" (team/dept, empty string if absent),\n'
        '    "dateStart" (e.g. "Jan 2023"), "dateEnd" (e.g. "Present"), '
        '"tasks" (array of bullet-point strings)\n'
        '- "education": array of objects, each with keys:\n'
        '    "degree" (credential name), "institution" (school), '
        '"program" (field/description, empty string if same as degree),\n'
        '    "dateStart", "dateEnd", "gpa" (empty string if absent)\n'
        '- "skills": array of objects, each with keys:\n'
        '    "category" (label), "technologies" (array of individual skill strings)\n\n'
        "Rules:\n"
        "- Use [] for absent arrays. Never return null for 'about'.\n"
        "- Do NOT wrap the JSON in markdown code fences.\n"
        "- Return only valid JSON.\n\n"
        f"Resume:\n{text}"
    )

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.4,
        ),
    )
    return json.loads(response.text)  # type: ignore[no-any-return]


def clear_resume_cache() -> None:
    """Invalidate the in-process cache so the next call to get_resume_data re-fetches the PDF."""
    _cache["data"] = None
    _cache["ts"] = 0.0


async def get_resume_data() -> dict[str, Any]:
    """Return parsed resume data, fetching and parsing only when the cache is stale."""
    now = time.monotonic()
    if _cache["data"] is not None and (now - _cache["ts"]) < _CACHE_TTL:
        logger.info("Returning cached resume data")
        return _cache["data"]  # type: ignore[return-value]

    if not RESUME_URL:
        raise ValueError("RESUME_URL is not configured")

    download_url = _normalise_url(RESUME_URL)
    logger.info("Fetching resume PDF from %s", download_url)

    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        resp = await client.get(download_url)
        resp.raise_for_status()
        pdf_bytes: bytes = resp.content

    logger.info("Extracting text from PDF (%d bytes)", len(pdf_bytes))
    text: str = await asyncio.to_thread(_extract_text, pdf_bytes)

    logger.info("Structuring resume with Gemini")
    data: dict[str, Any] = await asyncio.to_thread(_parse_with_gemini, text)

    _cache["data"] = data
    _cache["ts"] = now
    logger.info("Resume data cached")
    return data
