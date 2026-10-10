from __future__ import annotations

import re


def chunk_pages(pages: list[dict], chunk_size: int = 800, overlap: int = 120) -> list[dict]:
    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("chunk_size must be positive and overlap must be in [0, chunk_size)")
    chunks: list[dict] = []
    step = chunk_size - overlap
    for page in pages:
        text = re.sub(r"\s+", " ", str(page.get("text", ""))).strip()
        for start in range(0, len(text), step):
            content = text[start:start + chunk_size].strip()
            if content:
                chunks.append({
                    "chunk_id": f"{page['source']}:{page['page']}:{start}",
                    "source": page["source"],
                    "page": page["page"],
                    "text": content,
                })
            if start + chunk_size >= len(text):
                break
    return chunks