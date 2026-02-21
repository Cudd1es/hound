"""FastAPI app used by Chrome extension and local tools."""

import logging
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

    try:
        result = parse_resume_file(filename=filename, content=content)
        logger.info(
            "resume parse result: filename=%s skills_count=%s extracted_chars=%s",
            filename,
            len(result.get("profile", {}).get("skills", [])),
            len(result.get("extracted_text", "")),
        )
        return result
    except ValueError as exc:
        logger.warning("resume parse failed: filename=%s reason=%s", filename, exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
