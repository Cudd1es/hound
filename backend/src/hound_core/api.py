"""FastAPI app used by Chrome extension and local tools."""

from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze")
def analyze(payload: AnalyzeRequest) -> dict[str, Any]:
    return analyze_posting(profile=payload.profile, posting_text=payload.posting_text)


@app.post("/resume/parse")
async def parse_resume(file: UploadFile = File(...)) -> dict[str, Any]:
    filename = file.filename or "resume"
    content = await file.read()

    try:
        return parse_resume_file(filename=filename, content=content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
