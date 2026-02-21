"""FastAPI app used by Chrome extension and local tools."""

from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

from .service import analyze_posting


class AnalyzeRequest(BaseModel):
    profile: dict[str, Any] = Field(default_factory=dict)
    posting_text: str


app = FastAPI(title="Hound API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze")
def analyze(payload: AnalyzeRequest) -> dict[str, Any]:
    return analyze_posting(profile=payload.profile, posting_text=payload.posting_text)
