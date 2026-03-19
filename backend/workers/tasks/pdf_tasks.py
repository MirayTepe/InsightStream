"""PDF processing Celery tasks."""

from workers.celery_app import celery_app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.database import Base
from app.core.exceptions import PDFProcessingError
from app.core.logging_config import get_logger
from app.models.db_models import Document, Chunk

logger = get_logger(__name__)

# Separate engine for Celery workers (sync)
_engine = create_engine(settings.database_url_sync, pool_pre_ping=True)
_Session = sessionmaker(bind=_engine, autocommit=False, autoflush=False)


def _get_session():
    return _Session()


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(PDFProcessingError,),
)
def process_pdf_task(
    self,
    document_id: str,
    storage_path: str,
    filename: str,
    num_pages: int,
    user_id: str,
) -> dict:
    """
    Async PDF processing: load file, chunk, embed, store vectors and chunks in DB.
    """
    from app.services.pdf_service import PDFService
    from app.services.ai_service import AIService
    from app.services.vector_service import VectorStore
    from app.services.storage_service import StorageService

    db = _get_session()
    try:
        # Update status
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            logger.error("Document %s not found", document_id)
            return {"status": "failed", "error": "Document not found"}

        doc.status = "processing"
        db.commit()

        # Load file from storage
        storage = StorageService()
        file_bytes = storage.load(storage_path)

        # Extract and chunk
        pdf_service = PDFService(
            chunk_size=settings.rag_chunk_size,
            chunk_overlap=settings.rag_chunk_overlap,
        )
        text, _ = pdf_service.extract_text(file_bytes)
        chunks = pdf_service.chunk_text(text)

        # Embed and store vectors
        ai_service = AIService()
        vector_store = VectorStore()
        embeddings = ai_service.embed_texts(chunks)
        vector_store.upsert(document_id, embeddings, chunks)

        # Persist chunks to DB (clear existing first)
        db.query(Chunk).filter(Chunk.document_id == document_id).delete()
        for i, content in enumerate(chunks):
            chunk = Chunk(
                document_id=document_id,
                content=content,
                chunk_index=i,
            )
            db.add(chunk)

        # Update document
        doc.num_chunks = len(chunks)
        doc.status = "ready"
        db.commit()

        logger.info("Processed document %s: %d chunks", document_id, len(chunks))
        return {"status": "ready", "num_chunks": len(chunks)}

    except Exception as exc:
        logger.exception("PDF processing failed for %s: %s", document_id, exc)
        db.rollback()
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.status = "failed"
            db.commit()
        raise self.retry(exc=exc) if self.request.retries < self.max_retries else exc
    finally:
        db.close()
