from hound_core.requirements import extract_requirements


def test_extract_requirements_from_bullets() -> None:
    text = "Requirements:\n- 3+ years with React\n- Strong SQL"

    rows = extract_requirements(text)

    assert len(rows) == 2
    assert rows[0]["id"] == "req-1"
    assert rows[0]["category"] == "must"
    assert rows[1]["text"] == "Strong SQL"


def test_extract_requirements_classifies_dimensions_for_rule_based_rows() -> None:
    text = (
        "Qualifications:\n"
        "- Ability to collaborate across teams and stakeholders\n"
        "- Ability to pass a background check\n"
        "- 3+ years building Python services"
    )

    rows = extract_requirements(text)

    assert rows[0]["dimension"] == "soft"
    assert rows[1]["dimension"] == "compliance"
    assert rows[2]["dimension"] == "technical"


class CaptureProvider:
    def __init__(self) -> None:
        self.received_text = ""

    def extract_requirements(self, posting_text: str):
        self.received_text = posting_text
        return [
            {
                "id": "r-1",
                "text": "Ability to meet Microsoft, customer, and team expectations.",
                "category": "other",
                "weight": 0.4,
                "dimension": "soft",
            },
            {
                "id": "r-2",
                "text": "Ability to meet Microsoft, customer, and team expectations.",
                "category": "other",
                "weight": 0.7,
                "dimension": "soft",
            },
            {
                "id": "r-3",
                "text": "Experience with Python",
                "category": "must",
                "weight": 1.0,
            },
        ]


def test_extract_requirements_sanitizes_noisy_jd_and_deduplicates_rows() -> None:
    provider = CaptureProvider()
    noisy_text = (
        "Microsoft Software Engineer II\n"
        "About the job\n"
        "Qualifications\n"
        "Required Qualifications\n"
        "Experience with Python\n"
        "About the company\n"
        "Microsoft has 27,623,435 followers\n"
        "More jobs\n"
    )

    rows = extract_requirements(noisy_text, provider=provider)

    assert "about the company" not in provider.received_text.lower()
    assert len(rows) == 2
    assert rows[0]["id"] == "req-1"
    assert rows[1]["id"] == "req-2"
    assert rows[0]["weight"] == 0.7
