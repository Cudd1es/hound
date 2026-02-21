from hound_core.resume import load_resume_profile


def test_load_resume_profile_normalizes_skills() -> None:
    profile = load_resume_profile(
        {
            "basics": {"name": "Ansel"},
            "skills": ["TypeScript", "React"],
            "experiences": [{"title": "Engineer", "years": 3}],
        }
    )

    assert profile["skills"] == ["typescript", "react"]
    assert profile["experiences"][0]["years"] == 3
