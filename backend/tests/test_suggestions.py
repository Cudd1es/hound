from hound_core.suggestions import generate_suggestions


def test_generate_suggestions_prioritizes_missing_must_requirement() -> None:
    rows = [
        {
            "requirement_id": "r1",
            "verdict": "not_met",
            "confidence": 0.9,
            "evidence": [],
            "gap_reason": "No direct evidence in resume profile.",
            "category": "must",
            "requirement_text": "5+ years production Python",
        },
        {
            "requirement_id": "r2",
            "verdict": "partial",
            "confidence": 0.6,
            "evidence": ["Token overlap: sql"],
            "gap_reason": "Related skill found but no direct evidence.",
            "category": "preferred",
            "requirement_text": "Advanced SQL tuning",
        },
    ]

    suggestions = generate_suggestions(rows)

    assert suggestions[0]["priority"] == "high"
    assert "r1" in suggestions[0]["message"]
    assert len(suggestions) == 2
