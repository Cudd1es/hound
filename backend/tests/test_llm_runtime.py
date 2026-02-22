from hound_core.llm_runtime import (
    create_match_provider,
    create_requirement_provider,
    create_resume_profile_provider,
    llm_matching_enabled,
    load_llm_runtime_config,
)
from hound_core.llm_ollama import OllamaMatchProvider, OllamaRequirementProvider, OllamaResumeProfileProvider
from hound_core.llm_openai import OpenAIMatchProvider, OpenAIRequirementProvider, OpenAIResumeProfileProvider


def test_runtime_selects_openai_provider_family(monkeypatch) -> None:
    monkeypatch.setenv("HOUND_LLM_PROVIDER", "openai")
    monkeypatch.setenv("HOUND_LLM_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.setenv("HOUND_LLM_API_KEY", "test-key")
    monkeypatch.setenv("HOUND_LLM_MODEL", "gpt-4o-mini")

    assert isinstance(create_requirement_provider(), OpenAIRequirementProvider)
    assert isinstance(create_resume_profile_provider(), OpenAIResumeProfileProvider)
    assert isinstance(create_match_provider(), OpenAIMatchProvider)


def test_runtime_selects_ollama_provider_family(monkeypatch) -> None:
    monkeypatch.setenv("HOUND_LLM_PROVIDER", "ollama")
    monkeypatch.setenv("HOUND_LLM_BASE_URL", "http://127.0.0.1:11434")
    monkeypatch.setenv("HOUND_LLM_MODEL", "gemma3:27b")

    assert isinstance(create_requirement_provider(), OllamaRequirementProvider)
    assert isinstance(create_resume_profile_provider(), OllamaResumeProfileProvider)
    assert isinstance(create_match_provider(), OllamaMatchProvider)


def test_runtime_supports_legacy_ollama_env_fallback(monkeypatch) -> None:
    monkeypatch.setenv("HOUND_LLM_PROVIDER", "ollama")
    monkeypatch.delenv("HOUND_LLM_BASE_URL", raising=False)
    monkeypatch.delenv("HOUND_LLM_MODEL", raising=False)
    monkeypatch.setenv("HOUND_OLLAMA_URL", "http://localhost:11434")
    monkeypatch.setenv("HOUND_OLLAMA_MODEL", "qwen2.5:14b")

    cfg = load_llm_runtime_config()

    assert cfg.base_url == "http://localhost:11434"
    assert cfg.model == "qwen2.5:14b"


def test_runtime_matching_toggle(monkeypatch) -> None:
    monkeypatch.setenv("HOUND_LLM_PROVIDER", "openai")
    monkeypatch.setenv("HOUND_LLM_MATCHING", "false")

    assert llm_matching_enabled() is False
