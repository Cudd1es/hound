from hound_core.matching import generate_report


def test_generate_report_scores_known_skill_match() -> None:
    profile = {"skills": ["react", "sql"]}
    requirements = [
        {"id": "r1", "text": "React", "category": "must", "weight": 1.0},
        {"id": "r2", "text": "Kubernetes", "category": "preferred", "weight": 0.5},
    ]

    report = generate_report(profile=profile, requirements=requirements)

    assert report["overall_score"] > 0
    assert report["rows"][0]["verdict"] == "met"
    assert report["rows"][1]["verdict"] == "not_met"
