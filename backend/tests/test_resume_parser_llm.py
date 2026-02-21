from io import BytesIO

from docx import Document

from hound_core.resume_parser import parse_resume_file


class FakeProfileProvider:
    def build_profile(self, _resume_text: str):
        return {
            "skills": ["python", "llm"],
            "experiences": [{"title": "Engineer", "years": 2}],
        }


def test_parse_resume_file_uses_profile_provider_when_given() -> None:
    doc = Document()
    doc.add_paragraph("anything")

    payload = BytesIO()
    doc.save(payload)

    result = parse_resume_file(
        filename="resume.docx",
        content=payload.getvalue(),
        profile_provider=FakeProfileProvider(),
    )

    assert result["used_llm"] is True
    assert result["profile"]["skills"] == ["llm", "python"]
