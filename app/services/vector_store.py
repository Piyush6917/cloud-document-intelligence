from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

import numpy as np


class VectorStore:
    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.index_path = directory / "index.faiss"
        self.metadata_path = directory / "metadata.json"
        self.index = None
        self.metadata: list[dict] = []

    def _faiss(self):
        try:
            import faiss
            return faiss
        except ImportError as exc:
            raise RuntimeError("faiss-cpu is required for indexing") from exc

    @property
    def is_ready(self) -> bool:
        return self.index is not None and bool(self.metadata)

    def build(self, embeddings: np.ndarray, metadata: Sequence[dict]) -> None:
        if len(embeddings) != len(metadata) or not len(embeddings):
            raise ValueError("Embeddings and metadata must be non-empty and have equal lengths")
        vectors = np.asarray(embeddings, dtype=np.float32)
        self.index = self._faiss().IndexFlatIP(vectors.shape[1])
        self.index.add(vectors)
        self.metadata = [dict(item) for item in metadata]

    def search(self, query: np.ndarray, top_k: int = 5) -> list[dict]:
        if self.index is None or not self.metadata:
            return []
        query_vector = np.asarray(query, dtype=np.float32).reshape(1, -1)
        if query_vector.shape[1] != self.index.d:
            raise ValueError("Query embedding dimension does not match the index")
        scores, positions = self.index.search(query_vector, min(top_k, len(self.metadata)))
        return [{**self.metadata[pos], "score": float(score)}
                for score, pos in zip(scores[0], positions[0]) if pos >= 0]

    def save(self) -> None:
        if self.index is None:
            raise ValueError("Cannot save an empty index")
        self.directory.mkdir(parents=True, exist_ok=True)
        self._faiss().write_index(self.index, str(self.index_path))
        self.metadata_path.write_text(json.dumps(self.metadata, ensure_ascii=False), encoding="utf-8")

    def load(self) -> bool:
        if not self.index_path.exists() or not self.metadata_path.exists():
            return False
        self.index = self._faiss().read_index(str(self.index_path))
        self.metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        if self.index.ntotal != len(self.metadata):
            raise RuntimeError("Vector index and metadata are inconsistent")
        return True