from pathlib import Path
import re

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from app.config import get_settings
from app.services.pdf_processor import document_id
from app.services.rag_pipeline import RAGPipeline

router = APIRouter()
settings = get_settings()
pipeline = RAGPipeline(settings.data_dir, settings.index_dir, settings.embedding_model,
                       settings.embedding_device, settings.chunk_size, settings.chunk_overlap)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=5, ge=1, le=20)


def _safe_name(filename: str | None) -> str:
    name = Path(filename or "").name
    if not name or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._ -]*\.pdf", name, re.IGNORECASE):
        raise HTTPException(status_code=400, detail="Only safe PDF filenames are accepted")
    return name


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "indexed": pipeline.store.is_ready}


@router.get("/documents")
def documents() -> list[dict]:
    return [{"name": p.name, "size": p.stat().st_size, "document_id": document_id(p)}
            for p in sorted(settings.data_dir.glob("*.pdf"))]


@router.post("/documents/upload", status_code=status.HTTP_201_CREATED)
async def upload(file: UploadFile = File(...)) -> dict:
    name = _safe_name(file.filename)
    if file.content_type not in (None, "application/pdf"):
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported")
    content = await file.read()
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(status_code=413, detail="PDF exceeds the configured upload limit")
    target = settings.data_dir / name
    target.write_bytes(content)
    return {"name": name, "size": len(content), "message": "Uploaded; index documents to process it"}


@router.post("/documents/index")
def index_documents() -> dict:
    try:
        return {"chunks": pipeline.index_documents()}
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/chat")
def chat(request: ChatRequest) -> dict:
    try:
        return pipeline.ask(request.question, request.top_k)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/documents/{name}")
def delete_document(name: str) -> dict:
    safe_name = _safe_name(name)
    target = settings.data_dir / safe_name
    if not target.exists():
        raise HTTPException(status_code=404, detail="Document not found")
    target.unlink()
    return {"message": "Document deleted; re-index to rebuild the vector index"}