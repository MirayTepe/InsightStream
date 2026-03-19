"""User repository for database operations."""

from app.models.db_models import User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User entity."""

    def __init__(self, db) -> None:
        super().__init__(User, db)

    def get_by_email(self, email: str) -> User | None:
        """Get user by email."""
        return self.db.query(User).filter(User.email == email).first()

    def increment_request_count(self, user_id: str) -> None:
        """Increment request count for usage tracking."""
        user = self.get_by_id(user_id)
        if user:
            user.request_count += 1
            self.db.commit()
