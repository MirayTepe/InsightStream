"""PDF upload and processing routes."""

from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.api.dependencies import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.db_models import Document, User
from app.models.pdf_models import PDFUploadResponse, PDFUploadAsyncResponse
from app.repositories.document_repository import DocumentRepository
from app.services.pdf_service import PDFService
from app.services.ai_service import AIService
from app.services.vector_service import VectorStore
from app.services.storage_service import StorageService
from app.services.task_service import TaskService
from sqlalchemy.orm import Session

router = APIRouter(prefix="/pdf", tags=["pdf"])

pdf_service = PDFService()
ai_service = AIService()
vector_store = VectorStore()
storage_service = StorageService()
task_service = TaskService()


def _validate_pdf(file: UploadFile, file_bytes: bytes) -> None:
    """Validate file type and size."""
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    if len(file_bytes) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size: {settings.max_upload_size_mb}MB",
        )


@router.post("/upload", response_model=PDFUploadResponse)
async def upload_pdf_sync(file: UploadFile = File(...)):
    """
    Sync upload: process immediately, return document_id.
    No auth required. Document not persisted to DB.
    """
    file_bytes = await file.read()
    _validate_pdf(file, file_bytes)

    text, num_pages = pdf_service.extract_text(file_bytes)
    chunks = pdf_service.chunk_text(text)
    embeddings = ai_service.embed_texts(chunks)

    document_id = str(uuid4())
    vector_store.upsert(document_id, embeddings, chunks)

    return PDFUploadResponse(
        document_id=document_id,
        num_pages=num_pages,
        num_chunks=len(chunks),
    )


@router.post("/upload/async", response_model=PDFUploadAsyncResponse)
async def upload_pdf_async(
    file: UploadFile = File(...),
    user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[Session, Depends(get_db)] = None,
) -> PDFUploadAsyncResponse:
    """
    Async upload: save file, create document record, queue Celery task.
    Requires authentication. Poll /pdf/job/{job_id} for status.
    """
    file_bytes = await file.read()
    _validate_pdf(file, file_bytes)

    document_id = str(uuid4())
    storage_path = storage_service.generate_path(user.id, document_id, file.filename or "doc.pdf")
    storage_service.save(file_bytes, storage_path)

    text, num_pages = pdf_service.extract_text(file_bytes)
    namespace = f"{user.id}/{document_id}"

    doc = Document(
        id=document_id,
        user_id=user.id,
        filename=file.filename or "document.pdf",
        storage_path=storage_path,
        num_pages=num_pages,
        num_chunks=0,
        vector_namespace=namespace,
        file_size_bytes=len(file_bytes),
        status="pending",
    )
    doc_repo = DocumentRepository(db)
    doc_repo.create(doc)

    try:
        from workers.tasks.pdf_tasks import process_pdf_task
    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail="Async processing unavailable. Ensure Celery worker is running.",
        ) from e

    try:
        task = process_pdf_task.delay(
        document_id=document_id,
        storage_path=storage_path,
        filename=file.filename or "document.pdf",
        num_pages=num_pages,
        user_id=user.id,
    )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Failed to queue PDF processing: {e}",
        ) from e

    return PDFUploadAsyncResponse(
        document_id=document_id,
        job_id=task.id,
    )


@router.get("/job/{job_id}")
def get_job_status(job_id: str):
    """Get Celery task status for async PDF processing."""
    return task_service.get_status(job_id)
