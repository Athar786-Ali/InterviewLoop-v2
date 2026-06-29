
import pytest

from app.core.exceptions import AppError
from app.services.resume_parser import MAX_RESUME_BYTES, ResumeParserService


def _make_minimal_pdf(text: str = "Software Engineer with Python experience") -> bytes:
    """Build a minimal valid single-page PDF with embedded text.

    Constructing a real PDF by hand keeps the test self-contained
    without requiring a fixture file on disk.
    """
    # Simplest possible PDF: one page, one text stream
    stream_content = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode()
    stream_len = len(stream_content)

    pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 << /Type /Font "
        b"/Subtype /Type1 /BaseFont /Helvetica >> >> >> >>\nendobj\n"
        + f"4 0 obj\n<< /Length {stream_len} >>\nstream\n".encode()
        + stream_content
        + b"\nendstream\nendobj\n"
        b"xref\n0 5\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        b"0000000266 00000 n \n"
        b"trailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n366\n%%EOF"
    )
    return pdf


def test_parse_text_returns_cleaned_text():
    parser = ResumeParserService()
    result = parser.parse_text("  Jane Doe\n\n\n\nBackend Engineer  ")
    assert result == "Jane Doe\n\nBackend Engineer"


def test_parse_text_raises_for_empty_input():
    parser = ResumeParserService()
    with pytest.raises(AppError) as exc:
        parser.parse_text("   \n\n  ")
    assert exc.value.code == "RESUME_EMPTY"


def test_parse_text_collapses_multiple_spaces():
    parser = ResumeParserService()
    result = parser.parse_text("Python   Django   FastAPI")
    assert result == "Python Django FastAPI"


def test_parse_text_collapses_excessive_newlines():
    parser = ResumeParserService()
    result = parser.parse_text("Skills\n\n\n\nPython\n\n\n\nDjango")
    assert result == "Skills\n\nPython\n\nDjango"


def test_parse_pdf_rejects_oversized_file():
    parser = ResumeParserService()
    oversized = b"x" * (MAX_RESUME_BYTES + 1)
    with pytest.raises(AppError) as exc:
        parser.parse_pdf(oversized)
    assert exc.value.code == "RESUME_TOO_LARGE"


def test_parse_pdf_rejects_invalid_bytes():
    parser = ResumeParserService()
    with pytest.raises(AppError) as exc:
        parser.parse_pdf(b"this is not a pdf at all")
    assert exc.value.code == "RESUME_PARSE_FAILED"
