from typing import Literal, List

from pydantic import BaseModel, Field


RAGMode = Literal["summary", "deep_dive", "explain_to_kid"]


class Message(BaseModel):
    role: str  # "user" | "assistant" | "system"
    content: str


class ChatRequest(BaseModel):
    document_id: str = Field(..., min_length=1)
    messages: List[Message]
    mode: RAGMode = "summary"


class ChatResponse(BaseModel):
    answer: str
    mode: RAGMode
    used_chunks: int

