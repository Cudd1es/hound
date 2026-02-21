"""Ollama-backed LLM providers for requirements and resume parsing."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any
from urllib import error, request

from .schemas import Requirement

_JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(?P<body>\{.*\}|\[.*\])\s*```", re.DOTALL)
_ALLOWED_CATEGORIES = {"must", "preferred", "responsibility", "other"}


class OllamaError(RuntimeError):
    """Raised when Ollama request/response is invalid."""


@dataclass(frozen=True)
class OllamaConfig:
    base_url: str
    model: str
    timeout_seconds: float

    @classmethod
    def from_env(cls) -> "OllamaConfig":
        base_url = os.getenv("HOUND_OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
        model = os.getenv("HOUND_OLLAMA_MODEL", "gemma3-27b")
        timeout_seconds = float(os.getenv("HOUND_OLLAMA_TIMEOUT_SECONDS", "120"))
        return cls(base_url=base_url, model=model, timeout_seconds=timeout_seconds)


class OllamaClient:
    def __init__(self, config: OllamaConfig | None = None):
        self.config = config or OllamaConfig.from_env()

    def _post_chat(self, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            url=f"{self.config.base_url}/api/chat",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=self.config.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except (error.URLError, TimeoutError) as exc:
            raise OllamaError(f"failed to call Ollama: {exc}") from exc

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise OllamaError("Ollama returned invalid JSON payload") from exc

        if not isinstance(parsed, dict):
            raise OllamaError("Ollama response is not a JSON object")

        return parsed

    def chat_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        payload = {
            "model": self.config.model,
            "stream": False,
            "format": "json",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "options": {"temperature": 0.1},
        }

        response = self._post_chat(payload)
        content = (
            response.get("message", {}).get("content")
            if isinstance(response.get("message"), dict)
            else response.get("response")
        )

        if not isinstance(content, str) or not content.strip():
            raise OllamaError("Ollama returned empty content")

        return _extract_json_dict(content)


def llm_provider_enabled() -> bool:
    provider = os.getenv("HOUND_LLM_PROVIDER", "rule").strip().lower()
    return provider in {"ollama", "auto"}


def _extract_json_dict(text: str) -> dict[str, Any]:
    stripped = text.strip()
    candidates = [stripped]

    fenced_match = _JSON_BLOCK_RE.search(stripped)
    if fenced_match:
        candidates.append(fenced_match.group("body").strip())

    if "{" in stripped and "}" in stripped:
        start = stripped.find("{")
        end = stripped.rfind("}")
        candidates.append(stripped[start : end + 1])

    for candidate in candidates:
        try:
            obj = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            return obj

    raise OllamaError("could not parse JSON object from model output")


def _clamp_weight(value: Any) -> float:
    try:
        weight = float(value)
    except (TypeError, ValueError):
        weight = 1.0
    return min(max(weight, 0.0), 1.0)


class OllamaRequirementProvider:
    def __init__(self, client: OllamaClient | Any | None = None):
        self.client = client or OllamaClient()

    def extract_requirements(self, posting_text: str) -> list[Requirement]:
        if not posting_text.strip():
            return []

        prompt_text = posting_text.strip()
        if len(prompt_text) > 16000:
            prompt_text = prompt_text[:16000]

        response = self.client.chat_json(
            system_prompt=(
                "Extract structured job requirements from posting text. "
                "Return JSON object: {\"requirements\": [{\"text\": str, \"category\": "
                "\"must|preferred|responsibility|other\", \"weight\": number between 0 and 1}]}"
            ),
            user_prompt=f"Job posting text:\n{prompt_text}",
        )

        raw_requirements = response.get("requirements")
        if not isinstance(raw_requirements, list):
            raise OllamaError("requirements field missing or invalid")

        requirements: list[Requirement] = []
        for item in raw_requirements:
            if not isinstance(item, dict):
                continue

            text = str(item.get("text", "")).strip()
            if not text:
                continue

            category = str(item.get("category", "must")).strip().lower()
            if category not in _ALLOWED_CATEGORIES:
                category = "other"

            requirements.append(
                {
                    "id": f"req-{len(requirements) + 1}",
                    "text": text,
                    "category": category,
                    "weight": _clamp_weight(item.get("weight", 1.0)),
                }
            )

        if not requirements:
            raise OllamaError("model returned no usable requirements")

        return requirements


class OllamaResumeProfileProvider:
    def __init__(self, client: OllamaClient | Any | None = None):
        self.client = client or OllamaClient()

    def build_profile(self, resume_text: str) -> dict[str, Any]:
        prompt_text = resume_text.strip()
        if len(prompt_text) > 16000:
            prompt_text = prompt_text[:16000]

        response = self.client.chat_json(
            system_prompt=(
                "Extract structured resume profile. "
                "Return JSON object: {\"skills\": [str], \"experiences\": [object]}. "
                "skills should be normalized technical skills only."
            ),
            user_prompt=f"Resume text:\n{prompt_text}",
        )

        raw_skills = response.get("skills", [])
        skills: list[str] = []
        if isinstance(raw_skills, list):
            skills = sorted({str(skill).strip().lower() for skill in raw_skills if str(skill).strip()})

        experiences = response.get("experiences", [])
        if not isinstance(experiences, list):
            experiences = []

        return {
            "skills": skills,
            "experiences": experiences,
        }
