from pathlib import Path

from .chunker import chunk_pages
from .embedding_service import EmbeddingService
from .pdf_processor import extract_text_from_pdf
from .vector_store import VectorStore


class RAGPipeline:
    def __init__(self, data_dir: Path, index_dir: Path, model_name: str,
                 device: str = "cpu", chunk_size: int = 800, chunk_overlap: int = 120) -> None:
        self.data_dir = data_dir
        self.embedder = EmbeddingService(model_name, device)
        self.store = VectorStore(index_dir)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.store.load()

    def index_documents(self) -> int:
        pages: list[dict] = []
        for pdf in sorted(self.data_dir.glob("*.pdf")):
            pages.extend(extract_text_from_pdf(pdf))
        chunks = chunk_pages(pages, self.chunk_size, self.chunk_overlap)
        if not chunks:
            raise ValueError("No extractable text found in the PDF directory")
        self.store.build(self.embedder.encode([item["text"] for item in chunks]), chunks)
        self.store.save()
        return len(chunks)

    def ask(self, question: str, top_k: int = 5) -> dict:
        if not question.strip():
            raise ValueError("Question must not be empty")
        results = self.store.search(self.embedder.encode_query(question), top_k)
        if not results:
            return {"answer": "The documents do not contain enough information.", "sources": []}
        context = "\n\n".join(f"[{item['source']} p.{item['page']}] {item['text']}" for item in results)
        return {"answer": context, "sources": results}