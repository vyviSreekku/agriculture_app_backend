from pathlib import Path
from threading import Lock
from typing import Optional

import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


from app.services.Embedding_and_Retrivel import rag_query

router = APIRouter(prefix="/chatbot", tags=["chatbot"])


_offline_bundle_cache = None
_offline_bundle_signature = None


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _minirag_storage_dir() -> Path:
    return _backend_root() / "minirag_storage"


def _dataset_paths() -> list[str]:
    root = _backend_root()
    files = [
        root / "app" / "dataset" / "pest.json",
        root / "app" / "dataset" / "weed.json",
        root / "app" / "dataset" / "village_plant_disease_dataset.json",
    ]
    return [str(path) for path in files if path.exists()]



from fastapi import Request

def _get_rag_from_app(request: Request):
    rag = getattr(request.app.state, "rag", None)
    if rag is None:
        raise RuntimeError("MiniRAG is not initialized. Please check server logs for errors.")
    return rag


def _build_offline_rag_bundle() -> dict:
    global _offline_bundle_cache, _offline_bundle_signature

    storage_dir = _minirag_storage_dir()
    vdb_path = storage_dir / "vdb_chunks.json"
    text_path = storage_dir / "kv_store_text_chunks.json"

    if not vdb_path.exists() or not text_path.exists():
        raise RuntimeError("MiniRAG storage files are missing; initialize the chatbot index first")

    signature = (
        int(vdb_path.stat().st_mtime),
        int(text_path.stat().st_mtime),
        vdb_path.stat().st_size,
        text_path.stat().st_size,
    )
    if _offline_bundle_cache is not None and _offline_bundle_signature == signature:
        return _offline_bundle_cache

    with vdb_path.open("r", encoding="utf-8") as vdb_file:
        vdb_data = json.load(vdb_file)
    with text_path.open("r", encoding="utf-8") as text_file:
        text_data = json.load(text_file)

    ids = [item.get("__id__") for item in vdb_data.get("data", []) if isinstance(item, dict) and item.get("__id__")]
    chunks = []
    for chunk_id in ids:
        record = text_data.get(chunk_id)
        if not isinstance(record, dict):
            continue
        content = record.get("content")
        if not content:
            continue
        chunks.append({"id": chunk_id, "content": content})

    bundle = {
        "version": f"{signature[0]}-{signature[1]}",
        "embedding_model": "Xenova/all-MiniLM-L6-v2",
        "embedding_dim": vdb_data.get("embedding_dim"),
        "matrix": vdb_data.get("matrix"),
        "chunks": chunks,
    }

    _offline_bundle_cache = bundle
    _offline_bundle_signature = signature
    return bundle


class ChatbotQueryRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=1000)


class ChatbotQueryResponse(BaseModel):
    question: str
    answer: str
    formatted_answer: list[str]


def _format_gemini_answer(answer: str) -> list[str]:
    """Convert Gemini text into a simple JSON-friendly line format."""
    if not answer:
        return []

    lines = [line.strip() for line in answer.splitlines()]
    return [line for line in lines if line]


@router.get("/health")
def chatbot_health():
    return {"status": "ok", "service": "chatbot"}



@router.get("/offline-rag-bundle")
def chatbot_offline_rag_bundle(request: Request):
    try:
        _get_rag_from_app(request)
        return _build_offline_rag_bundle()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Offline RAG bundle failed: {exc}") from exc



@router.post("/query", response_model=ChatbotQueryResponse)
def chatbot_query(payload: ChatbotQueryRequest, request: Request):
    question = payload.question.strip()

    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        rag = _get_rag_from_app(request)
        answer = rag_query(rag, question)
        return ChatbotQueryResponse(
            question=question,
            answer=answer,
            formatted_answer=_format_gemini_answer(answer),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Chatbot query failed: {exc}") from exc
