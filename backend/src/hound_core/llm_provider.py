"""Provider protocols for optional LLM-powered extraction."""

from typing import Any
from typing import Protocol

from .schemas import MatchRow, Requirement


class RequirementProvider(Protocol):
    def extract_requirements(self, posting_text: str) -> list[Requirement]:
        """Extract structured requirements from posting text."""
        ...


class ResumeProfileProvider(Protocol):
    def build_profile(self, resume_text: str) -> dict[str, object]:
        """Build structured resume profile from plain text."""
        ...


class MatchProvider(Protocol):
    def match_requirements(self, profile: dict[str, Any], requirements: list[Requirement]) -> list[MatchRow]:
        """Match profile against requirements and return row-level verdicts."""
        ...
