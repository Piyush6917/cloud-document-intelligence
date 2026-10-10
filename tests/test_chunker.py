from app.services.chunker import chunk_pages


def test_chunker_preserves_metadata_and_rejects_bad_overlap():
    pages = [{"source": "guide.pdf", "page": 2, "text": "word " * 300}]
    chunks = chunk_pages(pages, chunk_size=50, overlap=10)
    assert chunks
    assert all(item["source"] == "guide.pdf" and item["page"] == 2 for item in chunks)


def test_chunker_rejects_overlap_larger_than_chunk():
    try:
        chunk_pages([], chunk_size=10, overlap=10)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected invalid overlap to raise")
