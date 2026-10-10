from __future__ import annotations

from typing import Sequence

import numpy as np


class EmbeddingService:
    def __init__(self, model_name: str, device: str = "cpu") -> None:
        self.model_name = model_name
        self.device = device
        self._model = None

    @property
    def model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                raise RuntimeError(
                    "sentence-transformers is required for indexing; install requirements.txt"
                ) from exc
            self._model = SentenceTransformer(self.model_name, device=self.device)
        return self._model

    def encode(self, texts: Sequence[str], batch_size: int = 32) -> np.ndarray:
        values = [text.strip() for text in texts]
        if not values or any(not value for value in values):
            raise ValueError("Cannot embed empty text")
        vectors = self.model.encode(
            values, batch_size=batch_size, normalize_embeddings=True,
            convert_to_numpy=True, show_progress_bar=False,
        )
        result = np.asarray(vectors, dtype=np.float32)
        if result.ndim != 2:
            raise RuntimeError("Embedding model returned an invalid shape")
        return result

    def encode_query(self, question: str) -> np.ndarray:
        return self.encode([question])[0]