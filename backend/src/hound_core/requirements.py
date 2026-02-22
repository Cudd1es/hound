"""Requirement extraction for job posting text."""

import logging
import re
from typing import Any

from .llm_runtime import create_requirement_provider
from .llm_provider import RequirementProvider
from .schemas import Requirement

_BULLET_PATTERN = re.compile(r"^\s*[-*•]\s+(?P<content>.+?)\s*$")
_SPACE_PATTERN = re.compile(r"\s+")
_HEADING_MARKERS = [
    "about the job",
    "overview",
    "responsibilities",
    "qualifications",
    "required qualifications",
    "preferred qualifications",
    "other requirements",
]
_TRUNCATION_MARKERS = [
    "about the company",
    "more jobs",
    "looking for talent",
    "linkedin corporation",
    "select language",
]
_NOISE_LINE_KEYWORDS = [
    "premium",
    "reactivate premium",
    "easy apply",
    "follow",
    "questions? visit our help center",
]
_CATEGORY_RANK = {"must": 0, "preferred": 1, "responsibility": 2, "other": 3}
_DIMENSION_RANK = {"technical": 0, "soft": 1, "compliance": 2, "other": 3}
_SOFT_KEYWORDS = [
    "communication",
    "collaborat",
    "stakeholder",
    "influenc",
    "team culture",
    "empathy",
    "bias towards action",
    "cross-team",
    "cross functional",
]
_COMPLIANCE_KEYWORDS = [
    "background check",
    "security screening",
    "clearance",
    "authorized to work",
    "work authorization",
    "work permit",
    "citizenship",
    "hybrid",
    "on-site",
    "onsite",
]
logger = logging.getLogger("hound.requirements")


def _clamp_weight(value: Any) -> float:
    try:
        weight = float(value)
    except (TypeError, ValueError):
        weight = 1.0
    return min(max(weight, 0.0), 1.0)


def _normalize_category(value: Any) -> str:
    category = str(value or "must").strip().lower()
    if category not in _CATEGORY_RANK:
        return "other"
    return category


def _infer_dimension(text: str) -> str:
    lowered = text.lower()
    if any(keyword in lowered for keyword in _COMPLIANCE_KEYWORDS):
        return "compliance"
    if any(keyword in lowered for keyword in _SOFT_KEYWORDS):
        return "soft"
    return "technical"


def _normalize_dimension(value: Any, text: str) -> str:
    dimension = str(value or "").strip().lower()
    if dimension in _DIMENSION_RANK:
        return dimension
    return _infer_dimension(text)


def _canonical_requirement_text(value: str) -> str:
    normalized = _SPACE_PATTERN.sub(" ", value.lower()).strip()
    return normalized.rstrip(" .;:!")


def _deduplicate_and_reindex_requirements(items: list[dict[str, Any]]) -> list[Requirement]:
    deduped: dict[str, Requirement] = {}

    for item in items:
        text = str(item.get("text", "")).strip()
        if not text:
            continue

        normalized_row: Requirement = {
            "id": "",
            "text": text,
            "category": _normalize_category(item.get("category")),
            "dimension": _normalize_dimension(item.get("dimension"), text),
            "weight": _clamp_weight(item.get("weight", 1.0)),
        }

        key = _canonical_requirement_text(text)
        existing = deduped.get(key)
        if existing is None:
            deduped[key] = normalized_row
            continue

        existing["weight"] = max(existing["weight"], normalized_row["weight"])
        if _CATEGORY_RANK[normalized_row["category"]] < _CATEGORY_RANK[existing["category"]]:
            existing["category"] = normalized_row["category"]
        if _DIMENSION_RANK[normalized_row["dimension"]] < _DIMENSION_RANK[existing["dimension"]]:
            existing["dimension"] = normalized_row["dimension"]

    results: list[Requirement] = []
    for index, row in enumerate(deduped.values(), start=1):
        row["id"] = f"req-{index}"
        results.append(row)

    return results


def _sanitize_posting_text(posting_text: str) -> str:
    text = posting_text.replace("\r\n", "\n").replace("\r", "\n")
    for marker in _HEADING_MARKERS + _TRUNCATION_MARKERS:
        text = re.sub(fr"(?i)\b{re.escape(marker)}\b", f"\n{marker.title()}\n", text)

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return posting_text.strip()

    start_index = 0
    for idx, line in enumerate(lines):
        lowered = line.lower()
        if any(marker in lowered for marker in _HEADING_MARKERS):
            start_index = idx
            break
    lines = lines[start_index:]

    end_index = len(lines)
    for idx, line in enumerate(lines):
        lowered = line.lower()
        if any(marker in lowered for marker in _TRUNCATION_MARKERS):
            end_index = idx
            break
    lines = lines[:end_index]

    filtered = []
    for line in lines:
        lowered = line.lower()
        if any(keyword in lowered for keyword in _NOISE_LINE_KEYWORDS):
            continue
        filtered.append(line)

    sanitized = "\n".join(filtered).strip()
    if not sanitized:
        return posting_text.strip()
    return sanitized


def _extract_requirements_rule_based(posting_text: str) -> list[Requirement]:
    requirements: list[dict[str, Any]] = []
    for line in posting_text.splitlines():
        match = _BULLET_PATTERN.match(line)
        if not match:
            continue

        requirements.append(
            {
                "text": match.group("content"),
                "category": "must",
                "dimension": _infer_dimension(match.group("content")),
                "weight": 1.0,
            }
        )

    return _deduplicate_and_reindex_requirements(requirements)


def extract_requirements(posting_text: str, provider: RequirementProvider | None = None) -> list[Requirement]:
    sanitized_posting_text = _sanitize_posting_text(posting_text)
    chosen_provider = provider or create_requirement_provider()

    if chosen_provider is not None:
        try:
            llm_rows = chosen_provider.extract_requirements(sanitized_posting_text)
            normalized_rows = _deduplicate_and_reindex_requirements(list(llm_rows))
            if normalized_rows:
                logger.info("requirements extracted via llm: count=%s", len(normalized_rows))
                return normalized_rows
            logger.warning("llm returned empty requirements; fallback to rule parser")
        except Exception as exc:  # noqa: BLE001 - keep service resilient
            logger.warning("llm requirements extraction failed; fallback to rule parser: %s", exc)

    return _extract_requirements_rule_based(sanitized_posting_text)
