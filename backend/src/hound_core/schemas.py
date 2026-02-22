"""Shared lightweight data contracts for core analysis."""

from typing import Literal, TypedDict


Verdict = Literal["met", "partial", "not_met", "unknown"]


class Requirement(TypedDict):
    id: str
    text: str
    category: Literal["must", "preferred", "responsibility", "other"]
    dimension: Literal["technical", "soft", "compliance", "other"]
    weight: float


class MatchRow(TypedDict):
    requirement_id: str
    verdict: Verdict
    confidence: float
    evidence: list[str]
    gap_reason: str | None
