from hound_core.requirements import extract_requirements


class BrokenProvider:
    def extract_requirements(self, _posting_text: str):
        raise RuntimeError("llm offline")


def test_extract_requirements_falls_back_when_provider_fails() -> None:
    text = "Requirements:\n- Python\n- SQL"

    rows = extract_requirements(text, provider=BrokenProvider())

    assert len(rows) == 2
    assert rows[0]["text"] == "Python"
