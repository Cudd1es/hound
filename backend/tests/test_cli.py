import json

from hound_core.cli import run_analysis


def test_run_analysis_reads_files_and_returns_report(tmp_path) -> None:
    resume_path = tmp_path / "resume.json"
    posting_path = tmp_path / "posting.txt"

    resume_path.write_text(
        json.dumps({"skills": ["React", "SQL"], "experiences": []}),
        encoding="utf-8",
    )
    posting_path.write_text("Requirements:\n- React\n- Kubernetes", encoding="utf-8")

    report = run_analysis(resume_path=resume_path, posting_path=posting_path)

    assert report["overall_score"] >= 0
    assert len(report["rows"]) == 2
    assert isinstance(report["suggestions"], list)
