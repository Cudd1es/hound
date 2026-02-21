"""Requirement extraction for job posting text."""

import logging
import re

from .llm_ollama import OllamaRequirementProvider, llm_provider_enabled
from .llm_provider import RequirementProvider
from .schemas import Requirement

_BULLET_PATTERN = re.compile(r"^\s*[-*•]\s+(?P<content>.+?)\s*$")
logger = logging.getLogger("hound.requirements")


def _extract_requirements_rule_based(posting_text: str) -> list[Requirement]:
    requirements: list[Requirement] = []
    for line in posting_text.splitlines():
        match = _BULLET_PATTERN.match(line)
        if not match:
            continue

        requirements.append(
            {
                "id": f"req-{len(requirements) + 1}",
                "text": match.group("content"),
                "category": "must",
                "weight": 1.0,
            }
        )

    return requirements


def extract_requirements(posting_text: str, provider: RequirementProvider | None = None) -> list[Requirement]:
    chosen_provider = provider
    if chosen_provider is None and llm_provider_enabled():
        chosen_provider = OllamaRequirementProvider()

    if chosen_provider is not None:
        try:
            llm_rows = chosen_provider.extract_requirements(posting_text)
            if llm_rows:
                logger.info("requirements extracted via llm: count=%s", len(llm_rows))
                return llm_rows
            logger.warning("llm returned empty requirements; fallback to rule parser")
        except Exception as exc:  # noqa: BLE001 - keep service resilient
            logger.warning("llm requirements extraction failed; fallback to rule parser: %s", exc)

    return _extract_requirements_rule_based(posting_text)
