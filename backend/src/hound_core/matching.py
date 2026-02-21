"""Matching and scoring utilities for resume-vs-posting analysis."""

import re
from typing import Any

from .schemas import MatchRow, Requirement

_WORD_RE = re.compile(r"[a-zA-Z0-9+#.]+")


def _tokens(value: str) -> set[str]:
    return {token.lower() for token in _WORD_RE.findall(value)}


def score_requirement(requirement: Requirement, profile: dict[str, Any]) -> MatchRow:
    requirement_text = requirement["text"].lower()
    requirement_tokens = _tokens(requirement_text)

    for skill in profile.get("skills", []):
        normalized_skill = str(skill).strip().lower()
        if not normalized_skill:
            continue
        if normalized_skill in requirement_text or requirement_text in normalized_skill:
            return {
                "requirement_id": requirement["id"],
                "verdict": "met",
                "confidence": 0.85,
                "evidence": [f"Matched skill: {normalized_skill}"],
                "gap_reason": None,
            }

    for skill in profile.get("skills", []):
        skill_tokens = _tokens(str(skill))
        if skill_tokens and skill_tokens.intersection(requirement_tokens):
            return {
                "requirement_id": requirement["id"],
                "verdict": "partial",
                "confidence": 0.6,
                "evidence": [f"Token overlap: {str(skill).strip().lower()}"],
                "gap_reason": "Related skill found but no direct evidence.",
            }

    return {
        "requirement_id": requirement["id"],
        "verdict": "not_met",
        "confidence": 0.7,
        "evidence": [],
        "gap_reason": "No direct evidence in resume profile.",
    }


def generate_report(profile: dict[str, Any], requirements: list[Requirement]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    total_weight = 0.0
    achieved_weight = 0.0

    for requirement in requirements:
        weight = float(requirement.get("weight", 1.0))
        row = score_requirement(requirement=requirement, profile=profile)
        row["category"] = requirement["category"]
        row["requirement_text"] = requirement["text"]
        rows.append(row)

        total_weight += weight
        if row["verdict"] == "met":
            achieved_weight += weight
        elif row["verdict"] == "partial":
            achieved_weight += weight * 0.5

    overall_score = int(round((achieved_weight / total_weight) * 100)) if total_weight > 0 else 0

    return {
        "overall_score": overall_score,
        "rows": rows,
    }
