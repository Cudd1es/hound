"""Provider protocol for optional LLM-powered extraction."""

from typing import Protocol

from .schemas import Requirement


class RequirementProvider(Protocol):
    def extract_requirements(self, posting_text: str) -> list[Requirement]:
        """Extract structured requirements from posting text."""
        ...
