"""Document repository for database operations."""

from app.models.db_models import Document
from app.repositories.base_repository import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    """Repository for Document entity."""

    def __init__(self, db) -> None:
        super().__init__(Document, db)

    def get_by_user_id(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Document]:
        """Get all documents for a user."""
        return (
            self.db.query(Document)
            .filter(Document.user_id == user_id)
            .order_by(Document.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_by_user_and_id(self, user_id: str, document_id: str) -> Document | None:
        """Get a document by ID only if it belongs to the user."""
        return (
            self.db.query(Document)
            .filter(Document.id == document_id, Document.user_id == user_id)
            .first()
        )
