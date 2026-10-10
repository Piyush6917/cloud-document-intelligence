
from pathlib import Path
import hashlib
import logging
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def extract_text_from_pdf(pdf_path: Path) -> list[dict]:
    """
    Extract text from a PDF, preserving its filename and page number.
    Page numbers are 1-based.
    """
    if not pdf_path.is_file() or pdf_path.suffix.lower() != ".pdf":
        raise ValueError(f"Not a PDF file: {pdf_path.name}")
    extracted_pages: list[dict] = []
    empty_pages = 0

    try:
        with fitz.open(pdf_path) as document:
            for page_number, page in enumerate(document, start=1):
                text = page.get_text("text").strip()

                if not text:
                    empty_pages += 1
                    continue

                extracted_pages.append({
                    "source": pdf_path.name,
                    "page": page_number,
                    "text": text,
                })

    except (fitz.FileDataError, OSError) as exc:
        raise RuntimeError(
            f"Failed to process {pdf_path.name}: {exc}"
        ) from exc
    if empty_pages:
        logger.warning("%s page(s) in %s have no extractable text; OCR may be required",
                       empty_pages, pdf_path.name)

    return extracted_pages


def document_id(pdf_path: Path) -> str:
    """Return a stable content identity without trusting a user-provided filename."""
    return hashlib.sha256(pdf_path.read_bytes()).hexdigest()


def process_all_pdfs(data_dir: Path = DATA_DIR) -> list[dict]:
    """Extract text from every PDF in the data directory."""
    if not data_dir.exists():
        raise FileNotFoundError(
            f"PDF directory not found: {data_dir}"
        )

    pdf_files = sorted(
        path for path in data_dir.iterdir()
        if path.is_file() and path.suffix.lower() == ".pdf"
    )

    if not pdf_files:
        raise FileNotFoundError(
            f"No PDF files found in {data_dir}"
        )

    all_pages = []

    for pdf_path in pdf_files:
        pages = extract_text_from_pdf(pdf_path)
        all_pages.extend(pages)

        print(
            f"{pdf_path.name}: extracted text from "
            f"{len(pages)} page(s)"
        )

    if not all_pages:
        raise ValueError(
            "No extractable text found. "
            "The PDFs may be scanned and require OCR."
        )

    print(f"\nTotal pages with extracted text: {len(all_pages)}")
    return all_pages


if __name__ == "__main__":
    pages = process_all_pdfs()

    print("\n--- Sample extracted text ---")
    print(f"Source: {pages[0]['source']}")
    print(f"Page: {pages[0]['page']}")
    print(pages[0]["text"][:1000])
