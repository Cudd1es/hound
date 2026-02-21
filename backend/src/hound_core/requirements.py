"""Requirement extraction for job posting text."""

import re

from .llm_provider import RequirementProvider
from .schemas import Requirement

_BULLET_PATTERN = re.compile(r"^\s*[-*•]\s+(?P<content>.+?)\s*$")


def extract_requirements(posting_text: str, provider: RequirementProvider | None = None) -> list[Requirement]:
    if provider is not None:
        return provider.extract_requirements(posting_text)

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
