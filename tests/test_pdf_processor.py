from pathlib import Path

import fitz

from app.services.pdf_processor import extract_text_from_pdf


def test_extract_text_from_pdf(tmp_path: Path):
    path = tmp_path / "sample.pdf"
    with fitz.open() as document:
        page = document.new_page()
        page.insert_text((72, 72), "Hello document")
        document.save(path)
    pages = extract_text_from_pdf(path)
    assert pages[0]["text"] == "Hello document"
    assert pages[0]["page"] == 1


def test_invalid_pdf_raises(tmp_path: Path):
    path = tmp_path / "invalid.pdf"
    path.write_text("not a pdf", encoding="utf-8")
    try:
        extract_text_from_pdf(path)
    except RuntimeError:
        pass
    else:
        raise AssertionError("Expected invalid PDF to raise")
