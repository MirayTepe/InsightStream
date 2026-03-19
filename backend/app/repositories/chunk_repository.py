"""Chunk repository for database operations."""

from app.models.db_models import Chunk
from app.repositories.base_repository import BaseRepository


class ChunkRepository(BaseRepository[Chunk]):
    """Repository for Chunk entity."""

    def __init__(self, db) -> None:
        super().__init__(Chunk, db)

    def get_by_document_id(self, document_id: str) -> list[Chunk]:
        """Get all chunks for a document ordered by index."""
        return (
            self.db.query(Chunk)
            .filter(Chunk.document_id == document_id)
            .order_by(Chunk.chunk_index)
            .all()
        )

    def delete_by_document_id(self, document_id: str) -> int:
        """Delete all chunks for a document. Returns count deleted."""
        count = self.db.query(Chunk).filter(Chunk.document_id == document_id).delete()
        self.db.commit()
        return count
