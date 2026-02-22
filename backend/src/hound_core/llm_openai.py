"""OpenAI-compatible LLM providers for requirements, resume parsing and matching."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib import error, request

from .schemas import MatchRow, Requirement

_ALLOWED_CATEGORIES = {"must", "preferred", "responsibility", "other"}
_ALLOWED_DIMENSIONS = {"technical", "soft", "compliance", "other"}
_ALLOWED_VERDICTS = {"met", "partial", "not_met", "unknown"}


class OpenAIProviderError(RuntimeError):
    """Raised when OpenAI-compatible request/response is invalid."""


@dataclass(frozen=True)
class OpenAIConfig:
    base_url: str
    model: str
    timeout_seconds: float
    api_key: str | None = None


def _extract_json_dict(text: str) -> dict[str, Any]:
    stripped = text.strip()
    candidates = [stripped]

    if "{" in stripped and "}" in stripped:
        start = stripped.find("{")
        end = stripped.rfind("}")
        candidates.append(stripped[start : end + 1])

    for candidate in candidates:
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload

    raise OpenAIProviderError("could not parse JSON object from model output")


def _clamp_weight(value: Any) -> float:
    try:
        weight = float(value)
    except (TypeError, ValueError):
        weight = 1.0
    return min(max(weight, 0.0), 1.0)


def _clamp_confidence(value: Any) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        confidence = 0.0
    return min(max(confidence, 0.0), 1.0)


class OpenAIClient:
    def __init__(self, config: OpenAIConfig):
        self.config = config

    def _chat_url(self) -> str:
        return f"{self.config.base_url.rstrip('/')}/chat/completions"

    def _post_chat(self, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        req = request.Request(
            url=self._chat_url(),
            data=body,
            headers=headers,
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=self.config.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except (error.URLError, TimeoutError) as exc:
            raise OpenAIProviderError(f"failed to call OpenAI-compatible API: {exc}") from exc

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise OpenAIProviderError("OpenAI-compatible API returned invalid JSON payload") from exc

        if not isinstance(parsed, dict):
            raise OpenAIProviderError("OpenAI-compatible response is not a JSON object")

        return parsed

    def chat_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }

        response = self._post_chat(payload)
        choices = response.get("choices")
        if not isinstance(choices, list) or not choices:
            raise OpenAIProviderError("OpenAI-compatible response has no choices")

        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise OpenAIProviderError("OpenAI-compatible choice payload is invalid")

        message = first_choice.get("message")
        if not isinstance(message, dict):
            raise OpenAIProviderError("OpenAI-compatible choice has no message")

        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise OpenAIProviderError("OpenAI-compatible API returned empty content")

        return _extract_json_dict(content)


class OpenAIRequirementProvider:
    def __init__(self, client: OpenAIClient | Any):
        self.client = client

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
                "\"must|preferred|responsibility|other\", \"dimension\": "
                "\"technical|soft|compliance|other\", \"weight\": number between 0 and 1}]}"
            ),
            user_prompt=f"Job posting text:\n{prompt_text}",
        )

        raw_requirements = response.get("requirements")
        if not isinstance(raw_requirements, list):
            raise OpenAIProviderError("requirements field missing or invalid")

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

            dimension = str(item.get("dimension", "technical")).strip().lower()
            if dimension not in _ALLOWED_DIMENSIONS:
                dimension = "other"

            requirements.append(
                {
                    "id": f"req-{len(requirements) + 1}",
                    "text": text,
                    "category": category,
                    "dimension": dimension,
                    "weight": _clamp_weight(item.get("weight", 1.0)),
                }
            )

        if not requirements:
            raise OpenAIProviderError("model returned no usable requirements")

        return requirements


class OpenAIResumeProfileProvider:
    def __init__(self, client: OpenAIClient | Any):
        self.client = client

    def build_profile(self, resume_text: str) -> dict[str, Any]:
        prompt_text = resume_text.strip()
        if len(prompt_text) > 16000:
            prompt_text = prompt_text[:16000]

        response = self.client.chat_json(
            system_prompt=(
                "Extract structured resume profile. "
                "Return JSON object: {\"skills\": [str], \"experiences\": [object], "
                "\"semantic_summary\": str, \"strengths\": [str], \"experience_signals\": [str]}. "
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

        semantic_summary = str(response.get("semantic_summary", "")).strip()

        strengths: list[str] = []
        raw_strengths = response.get("strengths", [])
        if isinstance(raw_strengths, list):
            strengths = [str(value).strip() for value in raw_strengths if str(value).strip()]

        experience_signals: list[str] = []
        raw_signals = response.get("experience_signals", [])
        if isinstance(raw_signals, list):
            experience_signals = [str(value).strip() for value in raw_signals if str(value).strip()]

        return {
            "skills": skills,
            "experiences": experiences,
            "semantic_summary": semantic_summary,
            "strengths": strengths,
            "experience_signals": experience_signals,
        }


class OpenAIMatchProvider:
    def __init__(self, client: OpenAIClient | Any):
        self.client = client

    def match_requirements(self, profile: dict[str, Any], requirements: list[Requirement]) -> list[MatchRow]:
        if not requirements:
            return []

        requirements_payload: list[dict[str, Any]] = []
        for requirement in requirements:
            requirements_payload.append(
                {
                    "id": requirement.get("id"),
                    "text": requirement.get("text"),
                    "category": requirement.get("category"),
                    "dimension": requirement.get("dimension"),
                    "weight": requirement.get("weight"),
                }
            )

        response = self.client.chat_json(
            system_prompt=(
                "Match resume profile to each requirement. "
                "Return JSON object: {\"matches\": [{\"requirement_id\": str, "
                "\"verdict\": \"met|partial|not_met|unknown\", \"confidence\": number between 0 and 1, "
                "\"evidence\": [str], \"gap_reason\": str|null}]}. "
                "Include one row per provided requirement id."
            ),
            user_prompt=(
                "Resume profile JSON:\n"
                f"{json.dumps(profile, ensure_ascii=False)}\n\n"
                "Requirements JSON:\n"
                f"{json.dumps(requirements_payload, ensure_ascii=False)}"
            ),
        )

        raw_matches = response.get("matches")
        if not isinstance(raw_matches, list):
            raise OpenAIProviderError("matches field missing or invalid")

        rows: list[MatchRow] = []
        for item in raw_matches:
            if not isinstance(item, dict):
                continue

            requirement_id = str(item.get("requirement_id", "")).strip()
            if not requirement_id:
                continue

            verdict = str(item.get("verdict", "unknown")).strip().lower()
            if verdict not in _ALLOWED_VERDICTS:
                verdict = "unknown"

            evidence: list[str] = []
            raw_evidence = item.get("evidence", [])
            if isinstance(raw_evidence, list):
                evidence = [str(value).strip() for value in raw_evidence if str(value).strip()]

            gap_reason_value = item.get("gap_reason")
            gap_reason = None if gap_reason_value is None else str(gap_reason_value).strip()
            if gap_reason == "":
                gap_reason = None

            rows.append(
                {
                    "requirement_id": requirement_id,
                    "verdict": verdict,
                    "confidence": _clamp_confidence(item.get("confidence", 0.0)),
                    "evidence": evidence,
                    "gap_reason": gap_reason,
                }
            )

        if not rows:
            raise OpenAIProviderError("model returned no usable matches")

        return rows
