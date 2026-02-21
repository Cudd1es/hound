"""Resume profile normalization helpers."""

from collections.abc import Mapping
from typing import Any


def load_resume_profile(input_profile: Mapping[str, Any]) -> dict[str, Any]:
    skills = [str(skill).strip().lower() for skill in input_profile.get("skills", []) if str(skill).strip()]

    return {
        **input_profile,
        "skills": skills,
        "experiences": list(input_profile.get("experiences", [])),
    }
