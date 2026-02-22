from hound_core.llm_ollama import (
    OllamaMatchProvider,
    OllamaRequirementProvider,
    OllamaResumeProfileProvider,
)


class FakeClient:
    def __init__(self, payload):
        self.payload = payload

    def chat_json(self, *_args, **_kwargs):
        return self.payload


def test_ollama_requirement_provider_normalizes_requirements() -> None:
    provider = OllamaRequirementProvider(
        client=FakeClient(
            {
                "requirements": [
                    {"text": "5+ years Python", "category": "must", "weight": 1.2},
                    {"text": "Kubernetes", "category": "preferred", "weight": 0.4},
                ]
            }
        )
    )

    rows = provider.extract_requirements("dummy posting")

    assert rows[0]["id"] == "req-1"
    assert rows[0]["weight"] == 1.0
    assert rows[1]["category"] == "preferred"


def test_ollama_resume_provider_normalizes_profile() -> None:
    provider = OllamaResumeProfileProvider(
        client=FakeClient(
            {
                "skills": ["Python", "FastAPI", "python"],
                "experiences": [{"title": "Engineer", "years": 3}],
                "semantic_summary": "Built and shipped Python systems.",
                "strengths": ["automation", "delivery"],
                "experience_signals": ["reduced latency by 40%"],
            }
        )
    )

    profile = provider.build_profile("dummy resume text")

    assert profile["skills"] == ["fastapi", "python"]
    assert profile["experiences"][0]["years"] == 3
    assert profile["semantic_summary"] == "Built and shipped Python systems."
    assert profile["strengths"] == ["automation", "delivery"]


def test_ollama_match_provider_normalizes_rows() -> None:
    provider = OllamaMatchProvider(
        client=FakeClient(
            {
                "matches": [
                    {
                        "requirement_id": "req-1",
                        "verdict": "MET",
                        "confidence": 1.2,
                        "evidence": ["Strong Python project alignment"],
                    },
                    {
                        "requirement_id": "req-2",
                        "verdict": "unsupported-value",
                        "confidence": "not-a-number",
                        "evidence": "not-a-list",
                        "gap_reason": 123,
                    },
                ]
            }
        )
    )

    rows = provider.match_requirements(
        profile={"skills": ["python"], "experiences": []},
        requirements=[
            {"id": "req-1", "text": "Python", "category": "must", "weight": 1.0},
            {"id": "req-2", "text": "Kubernetes", "category": "preferred", "weight": 0.5},
        ],
    )

    assert rows[0]["verdict"] == "met"
    assert rows[0]["confidence"] == 1.0
    assert rows[1]["verdict"] == "unknown"
    assert rows[1]["confidence"] == 0.0
    assert rows[1]["evidence"] == []
