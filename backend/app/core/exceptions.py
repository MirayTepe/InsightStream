class InsightStreamError(Exception):
    """Base application exception."""


class PDFProcessingError(InsightStreamError):
    """Raised when PDF extraction fails."""


class EmbeddingError(InsightStreamError):
    """Raised when embedding generation or vector operations fail."""


class RAGError(InsightStreamError):
    """Raised when the RAG pipeline fails."""


class NotFoundError(InsightStreamError):
    """Raised when a resource is not found."""


class UnauthorizedError(InsightStreamError):
    """Raised when authentication fails."""


class ForbiddenError(InsightStreamError):
    """Raised when user lacks permission for an action."""


class ValidationError(InsightStreamError):
    """Raised when input validation fails."""

