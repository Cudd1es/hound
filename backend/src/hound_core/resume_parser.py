"""Resume document parsing for PDF/DOCX uploads."""

from __future__ import annotations

import logging
from io import BytesIO
from pathlib import Path
from typing import Any

from docx import Document
from pypdf import PdfReader

from .llm_ollama import OllamaResumeProfileProvider, llm_provider_enabled
from .llm_provider import ResumeProfileProvider

_KNOWN_SKILLS = [
    "python",
    "fastapi",
    "flask",
    "django",
    "sql",
    "postgresql",
    "mysql",
    "mongodb",
    "redis",
    "kubernetes",
    "docker",
    "aws",
    "gcp",
    "azure",
    "typescript",
    "javascript",
    "react",
    "node",
    "spark",
    "airflow",
    "etl",
]
logger = logging.getLogger("hound.resume_parser")


def _normalize_text_list(value: Any, *, lowercase: bool = False) -> list[str]:
    if not isinstance(value, list):
        return []
    normalized: list[str] = []
    seen: set[str] = set()
    for raw in value:
        text = str(raw).strip()
        if not text:
            continue
        if lowercase:
            text = text.lower()
        key = text.lower() if not lowercase else text
        if key in seen:
            continue
        seen.add(key)
        normalized.append(text)
    return normalized


def _rule_semantic_summary(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return ""
    summary = " ".join(lines[:3]).strip()
    return summary[:380]


def _extract_text_from_docx(content: bytes) -> str:
    document = Document(BytesIO(content))
    lines = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
    return "\n".join(lines)


def _extract_text_from_pdf(content: bytes) -> str:
    reader = PdfReader(BytesIO(content))
    lines: list[str] = []
    for page in reader.pages:
        text = (page.extract_text() or "").strip()
        if text:
            lines.append(text)
    return "\n".join(lines)


def _extract_skills(text: str) -> list[str]:
    lowered = text.lower()
    skills = [skill for skill in _KNOWN_SKILLS if skill in lowered]
    return sorted(set(skills))


def _rule_based_profile(text: str) -> dict[str, Any]:
    skills = _extract_skills(text)
    return {
        "skills": skills,
        "experiences": [],
        "semantic_summary": _rule_semantic_summary(text),
        "strengths": skills[:6],
        "experience_signals": [],
    }


def parse_resume_file(
    filename: str,
    content: bytes,
    profile_provider: ResumeProfileProvider | None = None,
) -> dict[str, object]:
    extension = Path(filename).suffix.lower()

    if extension == ".docx":
        extracted_text = _extract_text_from_docx(content)
    elif extension == ".pdf":
        extracted_text = _extract_text_from_pdf(content)
    else:
        raise ValueError("Only .pdf and .docx files are supported.")

    used_llm = False
    profile = _rule_based_profile(extracted_text)

    chosen_provider = profile_provider
    if chosen_provider is None and llm_provider_enabled():
        chosen_provider = OllamaResumeProfileProvider()

    if chosen_provider is not None:
        try:
            llm_profile = chosen_provider.build_profile(extracted_text)
            llm_skills = sorted(_normalize_text_list(llm_profile.get("skills", []), lowercase=True))
            llm_experiences = llm_profile.get("experiences", [])
            if not isinstance(llm_experiences, list):
                llm_experiences = []

            semantic_summary = str(llm_profile.get("semantic_summary", "")).strip()
            strengths = _normalize_text_list(llm_profile.get("strengths", []), lowercase=False)
            experience_signals = _normalize_text_list(llm_profile.get("experience_signals", []), lowercase=False)

            profile = {
                "skills": llm_skills or profile["skills"],
                "experiences": llm_experiences,
                "semantic_summary": semantic_summary or profile.get("semantic_summary", ""),
                "strengths": strengths or profile.get("strengths", []),
                "experience_signals": experience_signals or profile.get("experience_signals", []),
            }
            used_llm = True
            logger.info("resume profile extracted via llm: skills_count=%s", len(profile["skills"]))
        except Exception as exc:  # noqa: BLE001 - keep service resilient
            logger.warning("llm resume parsing failed; fallback to rule parser: %s", exc)

    profile["source"] = filename
    return {
        "profile": profile,
        "extracted_text": extracted_text,
        "used_llm": used_llm,
    }
