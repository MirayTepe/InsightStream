"""Chat history repository for database operations."""

from app.models.db_models import ChatHistory
from app.repositories.base_repository import BaseRepository


class ChatRepository(BaseRepository[ChatHistory]):
    """Repository for ChatHistory entity."""

    def __init__(self, db) -> None:
        super().__init__(ChatHistory, db)

    def get_by_session(
        self,
        document_id: str,
        session_id: str,
        limit: int = 50,
    ) -> list[ChatHistory]:
        """Get chat history for a document session."""
        return (
            self.db.query(ChatHistory)
            .filter(
                ChatHistory.document_id == document_id,
                ChatHistory.session_id == session_id,
            )
            .order_by(ChatHistory.created_at.asc())
            .limit(limit)
            .all()
        )
