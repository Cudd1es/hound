from hound_core.llm_ollama import OllamaRequirementProvider, OllamaResumeProfileProvider


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
            }
        )
    )

    profile = provider.build_profile("dummy resume text")

    assert profile["skills"] == ["fastapi", "python"]
    assert profile["experiences"][0]["years"] == 3
