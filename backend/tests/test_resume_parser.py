from io import BytesIO

from docx import Document

from hound_core.resume_parser import parse_resume_file


def test_parse_resume_docx_extracts_known_skills() -> None:
    doc = Document()
    doc.add_paragraph("Software Engineer with Python FastAPI and SQL experience")

    buffer = BytesIO()
    doc.save(buffer)

    result = parse_resume_file(filename="resume.docx", content=buffer.getvalue())

    assert "python" in result["profile"]["skills"]
    assert "fastapi" in result["profile"]["skills"]
    assert "sql" in result["profile"]["skills"]
    assert result["profile"]["source"] == "resume.docx"
