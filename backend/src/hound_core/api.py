"""FastAPI app used by Chrome extension and local tools."""

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .logging_setup import configure_logging
from .resume_parser import parse_resume_file
from .service import analyze_posting


class AnalyzeRequest(BaseModel):
    profile: dict[str, Any] = Field(default_factory=dict)
    posting_text: str


app = FastAPI(title="Hound API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
log_path = configure_logging()
logger = logging.getLogger("hound.api")
logger.info("logging initialized at %s", log_path)

_RESUME_CACHE_SCHEMA_VERSION = 1


def _resume_cache_path() -> Path:
    return Path(os.getenv("HOUND_RESUME_CACHE_PATH", "logs/resume-parse-cache.json"))


def _resume_content_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _load_resume_cache(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("resume cache read failed: path=%s error=%s", path, exc)
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _save_resume_cache(path: Path, payload: dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    except OSError as exc:
        logger.warning("resume cache write failed: path=%s error=%s", path, exc)


def _cache_hit_result(cache_payload: dict[str, Any], file_hash: str) -> dict[str, Any] | None:
    if cache_payload.get("schema_version") != _RESUME_CACHE_SCHEMA_VERSION:
        return None
    if cache_payload.get("file_hash") != file_hash:
        return None
    result = cache_payload.get("result")
    if not isinstance(result, dict):
        return None
    return {
        **result,
        "cache_hit": True,
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze")
def analyze(payload: AnalyzeRequest) -> dict[str, Any]:
    logger.info(
        "analyze request: posting_chars=%s skills_count=%s",
        len(payload.posting_text),
        len(payload.profile.get("skills", [])),
    )
    result = analyze_posting(profile=payload.profile, posting_text=payload.posting_text)
    logger.info(
        "analyze result: score=%s rows=%s suggestions=%s",
        result.get("overall_score"),
        len(result.get("rows", [])),
        len(result.get("suggestions", [])),
    )
    return result


@app.post("/resume/parse")
async def parse_resume(file: UploadFile = File(...)) -> dict[str, Any]:
    filename = file.filename or "resume"
    content = await file.read()
    logger.info("resume parse request: filename=%s bytes=%s", filename, len(content))
    content_hash = _resume_content_hash(content)
    cache_path = _resume_cache_path()

    cached_payload = _load_resume_cache(cache_path)
    if cached_payload is not None:
        cached_result = _cache_hit_result(cached_payload, content_hash)
        if cached_result is not None:
            logger.info("resume parse cache hit: filename=%s hash=%s", filename, content_hash[:12])
            return cached_result

    try:
        result = parse_resume_file(filename=filename, content=content)
        _save_resume_cache(
            cache_path,
            {
                "schema_version": _RESUME_CACHE_SCHEMA_VERSION,
                "file_hash": content_hash,
                "filename": filename,
                "result": result,
            },
        )
        response = {
            **result,
            "cache_hit": False,
        }
        logger.info(
            "resume parse result: filename=%s skills_count=%s extracted_chars=%s used_llm=%s cache_hit=%s",
            filename,
            len(result.get("profile", {}).get("skills", [])),
            len(result.get("extracted_text", "")),
            result.get("used_llm", False),
            False,
        )
        return response
    except ValueError as exc:
        logger.warning("resume parse failed: filename=%s reason=%s", filename, exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
