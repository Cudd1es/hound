"""FastAPI app used by Chrome extension and local tools."""

import hashlib
import json
import logging
import os
from pathlib import Path
import time
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

_RESUME_CACHE_SCHEMA_VERSION = 2


def _resume_cache_max_entries() -> int:
    raw = os.getenv("HOUND_RESUME_CACHE_MAX_ENTRIES", "8").strip()
    try:
        value = int(raw)
    except ValueError:
        value = 8
    return max(1, min(value, 256))


def _resume_cache_path() -> Path:
    return Path(os.getenv("HOUND_RESUME_CACHE_PATH", "logs/resume-parse-cache.json"))


def _resume_content_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _new_resume_cache_payload() -> dict[str, Any]:
    return {"schema_version": _RESUME_CACHE_SCHEMA_VERSION, "entries": {}, "order": []}


def _load_resume_cache(path: Path) -> dict[str, Any]:
    if not path.exists():
        return _new_resume_cache_payload()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("resume cache read failed: path=%s error=%s", path, exc)
        return _new_resume_cache_payload()
    if not isinstance(payload, dict):
        return _new_resume_cache_payload()

    if payload.get("schema_version") == _RESUME_CACHE_SCHEMA_VERSION:
        entries = payload.get("entries")
        order = payload.get("order")
        if isinstance(entries, dict) and isinstance(order, list):
            return payload

    # Backward compatibility: migrate single-entry schema.
    file_hash = str(payload.get("file_hash", "")).strip()
    result = payload.get("result")
    if file_hash and isinstance(result, dict):
        migrated = _new_resume_cache_payload()
        migrated["entries"][file_hash] = {
            "filename": str(payload.get("filename", "")),
            "updated_at": time.time(),
            "result": result,
        }
        migrated["order"] = [file_hash]
        return migrated

    return _new_resume_cache_payload()


def _save_resume_cache(path: Path, payload: dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    except OSError as exc:
        logger.warning("resume cache write failed: path=%s error=%s", path, exc)


def _cache_hit_result(cache_payload: dict[str, Any], file_hash: str, filename: str) -> dict[str, Any] | None:
    if cache_payload.get("schema_version") != _RESUME_CACHE_SCHEMA_VERSION:
        return None
    entries = cache_payload.get("entries")
    if not isinstance(entries, dict):
        return None
    entry = entries.get(file_hash)
    if not isinstance(entry, dict):
        return None
    result = entry.get("result")
    if not isinstance(result, dict):
        return None

    profile = result.get("profile")
    if isinstance(profile, dict):
        result = {
            **result,
            "profile": {
                **profile,
                "source": filename,
            },
        }

    return {
        **result,
        "cache_hit": True,
    }


def _upsert_resume_cache_entry(
    cache_payload: dict[str, Any],
    file_hash: str,
    filename: str,
    result: dict[str, Any],
    max_entries: int,
) -> None:
    entries = cache_payload.get("entries")
    order = cache_payload.get("order")
    if not isinstance(entries, dict) or not isinstance(order, list):
        cache_payload.clear()
        cache_payload.update(_new_resume_cache_payload())
        entries = cache_payload["entries"]
        order = cache_payload["order"]

    entries[file_hash] = {
        "filename": filename,
        "updated_at": time.time(),
        "result": result,
    }

    order = [value for value in order if isinstance(value, str) and value != file_hash]
    order.append(file_hash)

    while len(order) > max_entries:
        oldest = order.pop(0)
        entries.pop(oldest, None)

    # Prune any orphan entries.
    for key in list(entries.keys()):
        if key not in order:
            entries.pop(key, None)

    cache_payload["entries"] = entries
    cache_payload["order"] = order


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
    cached_result = _cache_hit_result(cached_payload, content_hash, filename)
    if cached_result is not None:
        logger.info("resume parse cache hit: filename=%s hash=%s", filename, content_hash[:12])
        return cached_result

    try:
        result = parse_resume_file(filename=filename, content=content)
        _upsert_resume_cache_entry(
            cache_payload=cached_payload,
            file_hash=content_hash,
            filename=filename,
            result=result,
            max_entries=_resume_cache_max_entries(),
        )
        _save_resume_cache(cache_path, cached_payload)
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
