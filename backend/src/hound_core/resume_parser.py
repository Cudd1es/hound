"""Resume document parsing for PDF/DOCX uploads."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from docx import Document
from pypdf import PdfReader

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


def parse_resume_file(filename: str, content: bytes) -> dict[str, object]:
    extension = Path(filename).suffix.lower()

    if extension == ".docx":
        extracted_text = _extract_text_from_docx(content)
    elif extension == ".pdf":
        extracted_text = _extract_text_from_pdf(content)
    else:
        raise ValueError("Only .pdf and .docx files are supported.")

    profile = {
        "skills": _extract_skills(extracted_text),
        "experiences": [],
        "source": filename,
    }
    return {
        "profile": profile,
        "extracted_text": extracted_text,
    }
