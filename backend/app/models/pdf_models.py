from typing import Literal

from pydantic import BaseModel, Field


class PDFUploadResponse(BaseModel):
    """Sync upload: immediate processing."""

    document_id: str
    num_pages: int
    num_chunks: int


class PDFUploadAsyncResponse(BaseModel):
    """Async upload: returns job_id to poll status."""

    document_id: str
    job_id: str
    status: Literal["pending"] = "pending"
    message: str = "PDF queued for processing. Poll /pdf/job/{job_id} for status."

