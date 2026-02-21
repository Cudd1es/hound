from hound_core.requirements import extract_requirements


def test_extract_requirements_from_bullets() -> None:
    text = "Requirements:\n- 3+ years with React\n- Strong SQL"

    rows = extract_requirements(text)

    assert len(rows) == 2
    assert rows[0]["id"] == "req-1"
    assert rows[0]["category"] == "must"
    assert rows[1]["text"] == "Strong SQL"
