"""FastAPI dependency injection for services and repositories."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.user_repository import UserRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.chat_repository import ChatRepository
from app.services.pdf_service import PDFService
from app.services.ai_service import AIService
from app.services.vector_service import VectorStore
from app.services.cache_service import CacheService
from app.services.storage_service import StorageService


def get_user_repository(
    db: Annotated[Session, Depends(get_db)],
) -> UserRepository:
    """Get UserRepository with DB session."""
    return UserRepository(db)


def get_document_repository(
    db: Annotated[Session, Depends(get_db)],
) -> DocumentRepository:
    """Get DocumentRepository with DB session."""
    return DocumentRepository(db)


def get_chunk_repository(
    db: Annotated[Session, Depends(get_db)],
) -> ChunkRepository:
    """Get ChunkRepository with DB session."""
    return ChunkRepository(db)


def get_chat_repository(
    db: Annotated[Session, Depends(get_db)],
) -> ChatRepository:
    """Get ChatRepository with DB session."""
    return ChatRepository(db)


def get_pdf_service() -> PDFService:
    """Get PDFService singleton."""
    return PDFService()


def get_ai_service() -> AIService:
    """Get AIService singleton."""
    return AIService()


def get_vector_store() -> VectorStore:
    """Get VectorStore singleton."""
    return VectorStore()


def get_cache_service() -> CacheService:
    """Get CacheService singleton."""
    return CacheService()


def get_storage_service() -> StorageService:
    """Get StorageService singleton."""
    return StorageService()
