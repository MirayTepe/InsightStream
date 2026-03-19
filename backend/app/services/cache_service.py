"""Redis cache service for RAG responses, embeddings, and session data."""

import json
from typing import Any, Optional

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class CacheService:
    """
    Redis-backed cache service.

    Handles:
    - RAG responses (keyed by query hash + document + mode)
    - Session chat history (optional)
    - Embeddings (optional, for repeated queries)

    Uses in-memory fallback when Redis is unavailable.
    """

    def __init__(self) -> None:
        self._redis = None
        self._in_memory: dict[str, str] = {}
        self._connect()

    def _connect(self) -> None:
        """Connect to Redis. Fall back to in-memory if unavailable."""
        try:
            import redis
            self._redis = redis.from_url(settings.redis_url)
            self._redis.ping()
        except Exception as e:
            logger.warning("Redis unavailable, using in-memory cache: %s", e)
            self._redis = None

    def get(self, key: str) -> Optional[str]:
        """Get value by key."""
        try:
            if self._redis:
                return self._redis.get(key)
            return self._in_memory.get(key)
        except Exception as e:
            logger.warning("Cache get failed: %s", e)
            return None

    def set(
        self,
        key: str,
        value: str,
        ttl_seconds: Optional[int] = 3600,
    ) -> bool:
        """Set value with optional TTL."""
        try:
            if self._redis:
                self._redis.setex(key, ttl_seconds or 0, value)
            else:
                self._in_memory[key] = value
            return True
        except Exception as e:
            logger.warning("Cache set failed: %s", e)
            return False

    def get_json(self, key: str) -> Optional[Any]:
        """Get and deserialize JSON value."""
        raw = self.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    def set_json(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = 3600,
    ) -> bool:
        """Serialize and set JSON value."""
        try:
            return self.set(key, json.dumps(value), ttl_seconds)
        except (TypeError, ValueError):
            return False

    def delete(self, key: str) -> bool:
        """Delete a key."""
        try:
            if self._redis:
                self._redis.delete(key)
            else:
                self._in_memory.pop(key, None)
            return True
        except Exception as e:
            logger.warning("Cache delete failed: %s", e)
            return False

    def invalidate_prefix(self, prefix: str) -> int:
        """Invalidate all keys matching prefix. Returns count deleted."""
        try:
            if self._redis:
                keys = list(self._redis.scan_iter(match=f"{prefix}*"))
                if keys:
                    return self._redis.delete(*keys)
                return 0
            count = sum(1 for k in list(self._in_memory) if k.startswith(prefix))
            for k in list(self._in_memory):
                if k.startswith(prefix):
                    del self._in_memory[k]
            return count
        except Exception as e:
            logger.warning("Cache invalidate_prefix failed: %s", e)
            return 0
