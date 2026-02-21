from io import BytesIO

from docx import Document
from fastapi.testclient import TestClient

from hound_core.api import app


def test_resume_parse_endpoint_returns_profile() -> None:
    doc = Document()
    doc.add_paragraph("Backend developer with Python and SQL")

    payload = BytesIO()
    doc.save(payload)

    client = TestClient(app)
    response = client.post(
        "/resume/parse",
        files={
            "file": (
                "resume.docx",
                payload.getvalue(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert "profile" in body
    assert "python" in body["profile"]["skills"]


def test_resume_parse_endpoint_rejects_non_document_file() -> None:
    client = TestClient(app)
    response = client.post(
        "/resume/parse",
        files={"file": ("resume.txt", b"plain text", "text/plain")},
    )
    assert response.status_code == 400
