"""Orchestration for end-to-end posting analysis."""

from typing import Any

from .matching import generate_report
from .requirements import extract_requirements
from .resume import load_resume_profile
from .suggestions import generate_suggestions


def analyze_posting(profile: dict[str, Any], posting_text: str) -> dict[str, Any]:
    normalized_profile = load_resume_profile(profile)
    requirements = extract_requirements(posting_text=posting_text)
    report = generate_report(profile=normalized_profile, requirements=requirements)
    report["suggestions"] = generate_suggestions(report["rows"])
    return report
