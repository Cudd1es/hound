from hound_core.llm_openai import OpenAIMatchProvider, OpenAIRequirementProvider, OpenAIResumeProfileProvider


class FakeClient:
    def __init__(self, payload):
        self.payload = payload

    def chat_json(self, *_args, **_kwargs):
        return self.payload


def test_openai_requirement_provider_normalizes_requirements() -> None:
    provider = OpenAIRequirementProvider(
        client=FakeClient(
            {
                "requirements": [
                    {"text": "Python", "category": "must", "dimension": "technical", "weight": 1.3},
                    {"text": "Communication", "category": "preferred", "dimension": "soft", "weight": 0.4},
                ]
            }
        )
    )

    rows = provider.extract_requirements("dummy posting")

    assert rows[0]["id"] == "req-1"
    assert rows[0]["weight"] == 1.0
    assert rows[1]["dimension"] == "soft"


def test_openai_resume_provider_normalizes_profile() -> None:
    provider = OpenAIResumeProfileProvider(
        client=FakeClient(
            {
                "skills": ["Python", "python", "FastAPI"],
                "experiences": [{"title": "Engineer"}],
                "semantic_summary": "Built backend systems.",
                "strengths": ["delivery"],
                "experience_signals": ["shipped projects"],
            }
        )
    )

    profile = provider.build_profile("dummy resume")

    assert profile["skills"] == ["fastapi", "python"]
    assert profile["semantic_summary"] == "Built backend systems."
    assert profile["strengths"] == ["delivery"]


def test_openai_match_provider_normalizes_rows() -> None:
    provider = OpenAIMatchProvider(
        client=FakeClient(
            {
                "matches": [
                    {
                        "requirement_id": "req-1",
                        "verdict": "MET",
                        "confidence": 1.5,
                        "evidence": ["Python service delivery"],
                    },
                    {
                        "requirement_id": "req-2",
                        "verdict": "bad-value",
                        "confidence": "bad",
                        "evidence": "bad",
                        "gap_reason": 123,
                    },
                ]
            }
        )
    )

    rows = provider.match_requirements(
        profile={"skills": ["python"], "experiences": []},
        requirements=[
            {"id": "req-1", "text": "Python", "category": "must", "dimension": "technical", "weight": 1.0},
            {"id": "req-2", "text": "Kubernetes", "category": "preferred", "dimension": "technical", "weight": 0.5},
        ],
    )

    assert rows[0]["verdict"] == "met"
    assert rows[0]["confidence"] == 1.0
    assert rows[1]["verdict"] == "unknown"
    assert rows[1]["confidence"] == 0.0
