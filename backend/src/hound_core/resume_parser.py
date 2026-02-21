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
    return {
        "skills": _extract_skills(text),
        "experiences": [],
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
            llm_skills = llm_profile.get("skills", [])
            if isinstance(llm_skills, list):
                profile = {
                    "skills": sorted(
                        {
                            str(skill).strip().lower()
                            for skill in llm_skills
                            if str(skill).strip()
                        }
                    ),
                    "experiences": llm_profile.get("experiences", []),
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
