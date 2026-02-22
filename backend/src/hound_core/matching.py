"""Matching and scoring utilities for resume-vs-posting analysis."""

import logging
import re
from typing import Any

from .llm_ollama import OllamaMatchProvider, llm_matching_enabled
from .llm_provider import MatchProvider
from .schemas import MatchRow, Requirement

_WORD_RE = re.compile(r"[a-zA-Z0-9+#.]+")
_DIMENSION_WEIGHT_MULTIPLIER = {
    "technical": 1.0,
    "soft": 0.45,
    "compliance": 0.2,
    "other": 0.65,
}
logger = logging.getLogger("hound.matching")


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


def _clamp_confidence(value: Any) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        confidence = 0.0
    return min(max(confidence, 0.0), 1.0)


def _normalize_llm_row(raw_row: dict[str, Any]) -> MatchRow:
    evidence: list[str] = []
    raw_evidence = raw_row.get("evidence", [])
    if isinstance(raw_evidence, list):
        evidence = [str(value).strip() for value in raw_evidence if str(value).strip()]

    gap_reason_value = raw_row.get("gap_reason")
    gap_reason = None if gap_reason_value is None else str(gap_reason_value).strip()
    if gap_reason == "":
        gap_reason = None

    verdict = str(raw_row.get("verdict", "unknown")).strip().lower()
    if verdict not in {"met", "partial", "not_met", "unknown"}:
        verdict = "unknown"

    return {
        "requirement_id": str(raw_row.get("requirement_id", "")).strip(),
        "verdict": verdict,
        "confidence": _clamp_confidence(raw_row.get("confidence", 0.0)),
        "evidence": evidence,
        "gap_reason": gap_reason,
    }


def _llm_rows_by_requirement_id(rows: list[MatchRow]) -> dict[str, MatchRow]:
    indexed: dict[str, MatchRow] = {}
    for raw_row in rows:
        row = _normalize_llm_row(raw_row)
        requirement_id = row["requirement_id"]
        if requirement_id:
            indexed[requirement_id] = row
    return indexed


def _effective_requirement_weight(requirement: Requirement) -> float:
    base_weight = float(requirement.get("weight", 1.0))
    dimension = str(requirement.get("dimension", "technical")).strip().lower()
    multiplier = _DIMENSION_WEIGHT_MULTIPLIER.get(dimension, _DIMENSION_WEIGHT_MULTIPLIER["other"])
    return base_weight * multiplier


def generate_report(
    profile: dict[str, Any],
    requirements: list[Requirement],
    match_provider: MatchProvider | None = None,
) -> dict[str, Any]:
    chosen_provider = match_provider
    if chosen_provider is None and llm_matching_enabled():
        chosen_provider = OllamaMatchProvider()

    llm_rows_map: dict[str, MatchRow] = {}
    if chosen_provider is not None:
        try:
            llm_rows = chosen_provider.match_requirements(profile, requirements)
            llm_rows_map = _llm_rows_by_requirement_id(llm_rows)
            if llm_rows_map:
                logger.info("matching via llm: rows=%s", len(llm_rows_map))
            else:
                logger.warning("llm matching returned no usable rows; fallback to rule matcher")
        except Exception as exc:  # noqa: BLE001 - keep service resilient
            logger.warning("llm matching failed; fallback to rule matcher: %s", exc)

    rows: list[dict[str, Any]] = []
    total_weight = 0.0
    achieved_weight = 0.0

    for requirement in requirements:
        effective_weight = _effective_requirement_weight(requirement)
        row = llm_rows_map.get(requirement["id"])
        if row is None:
            row = score_requirement(requirement=requirement, profile=profile)
        row["category"] = requirement["category"]
        row["dimension"] = requirement.get("dimension", "technical")
        row["requirement_text"] = requirement["text"]
        rows.append(row)

        if row["verdict"] != "unknown":
            total_weight += effective_weight
        if row["verdict"] == "met":
            achieved_weight += effective_weight
        elif row["verdict"] == "partial":
            achieved_weight += effective_weight * 0.5

    overall_score = int(round((achieved_weight / total_weight) * 100)) if total_weight > 0 else 0

    return {
        "overall_score": overall_score,
        "rows": rows,
    }
