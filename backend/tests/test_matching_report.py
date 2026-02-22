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


class FakeMatchProvider:
    def match_requirements(self, _profile, _requirements):
        return [
            {
                "requirement_id": "r1",
                "verdict": "met",
                "confidence": 0.95,
                "evidence": ["semantic alignment"],
                "gap_reason": None,
            },
            {
                "requirement_id": "r2",
                "verdict": "partial",
                "confidence": 0.65,
                "evidence": ["related production signals"],
                "gap_reason": "Missing direct ownership detail.",
            },
        ]


class BrokenMatchProvider:
    def match_requirements(self, _profile, _requirements):
        raise RuntimeError("llm offline")


def test_generate_report_prefers_llm_matching_when_provider_is_given() -> None:
    profile = {"skills": ["react", "sql"]}
    requirements = [
        {"id": "r1", "text": "React", "category": "must", "weight": 1.0},
        {"id": "r2", "text": "Kubernetes", "category": "preferred", "weight": 0.5},
    ]

    report = generate_report(profile=profile, requirements=requirements, match_provider=FakeMatchProvider())

    assert report["rows"][0]["verdict"] == "met"
    assert report["rows"][1]["verdict"] == "partial"
    assert report["rows"][1]["gap_reason"] == "Missing direct ownership detail."
    assert report["overall_score"] == 83


def test_generate_report_falls_back_to_rule_matching_when_provider_fails() -> None:
    profile = {"skills": ["react", "sql"]}
    requirements = [
        {"id": "r1", "text": "React", "category": "must", "weight": 1.0},
        {"id": "r2", "text": "Kubernetes", "category": "preferred", "weight": 0.5},
    ]

    report = generate_report(profile=profile, requirements=requirements, match_provider=BrokenMatchProvider())

    assert report["rows"][0]["verdict"] == "met"
    assert report["rows"][1]["verdict"] == "not_met"


class WeightedVerdictProvider:
    def match_requirements(self, _profile, _requirements):
        return [
            {
                "requirement_id": "r1",
                "verdict": "met",
                "confidence": 0.95,
                "evidence": ["Strong technical match"],
                "gap_reason": None,
            },
            {
                "requirement_id": "r2",
                "verdict": "not_met",
                "confidence": 0.7,
                "evidence": [],
                "gap_reason": "No clear soft-skill phrasing.",
            },
            {
                "requirement_id": "r3",
                "verdict": "unknown",
                "confidence": 0.4,
                "evidence": [],
                "gap_reason": "No direct signal.",
            },
        ]


def test_generate_report_excludes_unknown_from_denominator_and_downweights_soft_compliance() -> None:
    profile = {"skills": ["python"]}
    requirements = [
        {"id": "r1", "text": "Python", "category": "must", "dimension": "technical", "weight": 1.0},
        {"id": "r2", "text": "Strong communication", "category": "preferred", "dimension": "soft", "weight": 1.0},
        {"id": "r3", "text": "Pass background check", "category": "other", "dimension": "compliance", "weight": 1.0},
    ]

    report = generate_report(profile=profile, requirements=requirements, match_provider=WeightedVerdictProvider())

    assert report["overall_score"] == 69
    assert report["rows"][2]["verdict"] == "unknown"
