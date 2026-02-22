"""Unified runtime config and provider selection for LLM backends."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

from .llm_ollama import (
    OllamaClient,
    OllamaConfig,
    OllamaMatchProvider,
    OllamaRequirementProvider,
    OllamaResumeProfileProvider,
)
from .llm_openai import (
    OpenAIClient,
    OpenAIConfig,
    OpenAIMatchProvider,
    OpenAIRequirementProvider,
    OpenAIResumeProfileProvider,
)
from .llm_provider import MatchProvider, RequirementProvider, ResumeProfileProvider

ProviderKind = Literal["disabled", "ollama", "openai"]


@dataclass(frozen=True)
class LLMRuntimeConfig:
    provider: ProviderKind
    base_url: str
    model: str
    api_key: str | None
    timeout_seconds: float
    matching_mode: str


def _first_non_empty(*values: str | None) -> str | None:
    for value in values:
        if value is None:
            continue
        stripped = value.strip()
        if stripped:
            return stripped
    return None


def _parse_float(value: str | None, default: float) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _normalize_provider(raw_provider: str) -> ProviderKind:
    lowered = raw_provider.strip().lower()
    if lowered in {"rule", "disabled", "none", "off"}:
        return "disabled"
    if lowered == "auto":
        has_api_key = bool(_first_non_empty(os.getenv("HOUND_LLM_API_KEY"), os.getenv("HOUND_OPENAI_API_KEY")))
        return "openai" if has_api_key else "ollama"
    if lowered in {"openai", "openai_api", "openai-compatible", "openai_compatible", "api"}:
        return "openai"
    if lowered in {"ollama", "local"}:
        return "ollama"
    return "disabled"


def load_llm_runtime_config() -> LLMRuntimeConfig:
    provider = _normalize_provider(os.getenv("HOUND_LLM_PROVIDER", "rule"))
    matching_mode = _first_non_empty(os.getenv("HOUND_LLM_MATCHING"), "auto") or "auto"

    if provider == "openai":
        base_url = _first_non_empty(
            os.getenv("HOUND_LLM_BASE_URL"),
            os.getenv("HOUND_OPENAI_BASE_URL"),
            "https://api.openai.com/v1",
        )
        model = _first_non_empty(
            os.getenv("HOUND_LLM_MODEL"),
            os.getenv("HOUND_OPENAI_MODEL"),
            "gpt-4o-mini",
        )
        timeout_seconds = _parse_float(
            _first_non_empty(
                os.getenv("HOUND_LLM_TIMEOUT_SECONDS"),
                os.getenv("HOUND_OPENAI_TIMEOUT_SECONDS"),
                os.getenv("HOUND_OLLAMA_TIMEOUT_SECONDS"),
            ),
            120.0,
        )
        api_key = _first_non_empty(os.getenv("HOUND_LLM_API_KEY"), os.getenv("HOUND_OPENAI_API_KEY"))
    elif provider == "ollama":
        base_url = _first_non_empty(
            os.getenv("HOUND_LLM_BASE_URL"),
            os.getenv("HOUND_OLLAMA_URL"),
            "http://127.0.0.1:11434",
        )
        model = _first_non_empty(
            os.getenv("HOUND_LLM_MODEL"),
            os.getenv("HOUND_OLLAMA_MODEL"),
            "gemma3:27b",
        )
        timeout_seconds = _parse_float(
            _first_non_empty(
                os.getenv("HOUND_LLM_TIMEOUT_SECONDS"),
                os.getenv("HOUND_OLLAMA_TIMEOUT_SECONDS"),
            ),
            120.0,
        )
        api_key = _first_non_empty(os.getenv("HOUND_LLM_API_KEY"))
    else:
        base_url = ""
        model = ""
        timeout_seconds = 0.0
        api_key = None

    return LLMRuntimeConfig(
        provider=provider,
        base_url=base_url or "",
        model=model or "",
        api_key=api_key,
        timeout_seconds=timeout_seconds,
        matching_mode=matching_mode.lower(),
    )


def llm_provider_enabled(config: LLMRuntimeConfig | None = None) -> bool:
    runtime_config = config or load_llm_runtime_config()
    return runtime_config.provider in {"ollama", "openai"}


def llm_matching_enabled(config: LLMRuntimeConfig | None = None) -> bool:
    runtime_config = config or load_llm_runtime_config()
    mode = runtime_config.matching_mode
    if mode in {"1", "true", "yes", "on"}:
        return True
    if mode in {"0", "false", "no", "off"}:
        return False
    return llm_provider_enabled(runtime_config)


def _create_ollama_client(config: LLMRuntimeConfig) -> OllamaClient:
    return OllamaClient(
        OllamaConfig(
            base_url=config.base_url,
            model=config.model,
            timeout_seconds=config.timeout_seconds,
        )
    )


def _create_openai_client(config: LLMRuntimeConfig) -> OpenAIClient:
    return OpenAIClient(
        OpenAIConfig(
            base_url=config.base_url,
            model=config.model,
            timeout_seconds=config.timeout_seconds,
            api_key=config.api_key,
        )
    )


def create_requirement_provider(config: LLMRuntimeConfig | None = None) -> RequirementProvider | None:
    runtime_config = config or load_llm_runtime_config()
    if runtime_config.provider == "disabled":
        return None
    if runtime_config.provider == "openai":
        return OpenAIRequirementProvider(client=_create_openai_client(runtime_config))
    return OllamaRequirementProvider(client=_create_ollama_client(runtime_config))


def create_resume_profile_provider(config: LLMRuntimeConfig | None = None) -> ResumeProfileProvider | None:
    runtime_config = config or load_llm_runtime_config()
    if runtime_config.provider == "disabled":
        return None
    if runtime_config.provider == "openai":
        return OpenAIResumeProfileProvider(client=_create_openai_client(runtime_config))
    return OllamaResumeProfileProvider(client=_create_ollama_client(runtime_config))


def create_match_provider(config: LLMRuntimeConfig | None = None) -> MatchProvider | None:
    runtime_config = config or load_llm_runtime_config()
    if runtime_config.provider == "disabled" or not llm_matching_enabled(runtime_config):
        return None
    if runtime_config.provider == "openai":
        return OpenAIMatchProvider(client=_create_openai_client(runtime_config))
    return OllamaMatchProvider(client=_create_ollama_client(runtime_config))
