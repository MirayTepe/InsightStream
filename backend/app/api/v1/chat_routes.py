"""Chat and RAG routes with streaming support."""

from typing import Annotated

import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response, StreamingResponse
from sse_starlette.sse import EventSourceResponse

from app.models.chat_models import ChatRequest, ChatResponse
from app.services.ai_service import AIService
from app.services.vector_service import VectorStore
from app.services.tts_service import TTSService
from app.core.config import settings

router = APIRouter(prefix="/chat", tags=["chat"])

ai_service = AIService()
vector_store = VectorStore()
tts_service = TTSService()


def _get_last_user_message(req: ChatRequest):
    return next((m for m in reversed(req.messages) if m.role == "user"), None)


@router.post("/ask", response_model=ChatResponse)
async def ask_chat(req: ChatRequest):
    """Non-streaming RAG response."""
    last_user = _get_last_user_message(req)
    if not last_user:
        raise HTTPException(status_code=400, detail="At least one user message is required.")

    query_emb = ai_service.embed_query(last_user.content)
    retrieved = vector_store.search(
        req.document_id,
        query_emb,
        k=settings.rag_default_top_k,
    )
    answer = ai_service.generate_answer(req.mode, last_user.content, retrieved)
    return ChatResponse(answer=answer, mode=req.mode, used_chunks=len(retrieved))


async def _stream_generator(req: ChatRequest):
    """Async generator for SSE chunks."""
    last_user = _get_last_user_message(req)
    if not last_user:
        yield {"event": "error", "data": json.dumps({"error": "No user message"})}
        return

    try:
        query_emb = ai_service.embed_query(last_user.content)
        retrieved = vector_store.search(
            req.document_id,
            query_emb,
            k=settings.rag_default_top_k,
        )
        yield {
            "event": "metadata",
            "data": json.dumps({"used_chunks": len(retrieved), "mode": req.mode}),
        }
        for chunk in ai_service.generate_answer_stream(
            req.mode, last_user.content, retrieved
        ):
            yield {"event": "token", "data": chunk}
        yield {"event": "done", "data": json.dumps({"status": "ok"})}
    except Exception as e:
        yield {"event": "error", "data": json.dumps({"error": str(e)})}


@router.post("/ask/stream")
async def ask_chat_stream(req: ChatRequest):
    """
    Streaming RAG response via Server-Sent Events.
    Events: metadata, token, done, error.
    """
    return EventSourceResponse(_stream_generator(req))


@router.post("/answer-audio")
async def answer_audio(req: ChatRequest):
    """Convert RAG response to audio (TTS)."""
    last_user = _get_last_user_message(req)
    if not last_user:
        raise HTTPException(status_code=400, detail="At least one user message is required.")

    query_emb = ai_service.embed_query(last_user.content)
    retrieved = vector_store.search(req.document_id, query_emb, k=settings.rag_default_top_k)
    answer = ai_service.generate_answer(req.mode, last_user.content, retrieved)
    audio_bytes = tts_service.synthesize(answer)
    return Response(content=audio_bytes, media_type="audio/mpeg")
