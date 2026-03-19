from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .exceptions import (
    PDFProcessingError,
    EmbeddingError,
    RAGError,
    InsightStreamError,
    NotFoundError,
    UnauthorizedError,
    ForbiddenError,
    ValidationError,
)


def init_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(PDFProcessingError)
    async def pdf_error_handler(_: Request, exc: PDFProcessingError):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(EmbeddingError)
    async def embedding_error_handler(_: Request, exc: EmbeddingError):
        return JSONResponse(
            status_code=500,
            content={"detail": "Embedding failed", "error": str(exc)},
        )

    @app.exception_handler(RAGError)
    async def rag_error_handler(_: Request, exc: RAGError):
        return JSONResponse(
            status_code=500,
            content={"detail": "RAG pipeline failed", "error": str(exc)},
        )

    @app.exception_handler(InsightStreamError)
    async def base_app_error_handler(_: Request, exc: InsightStreamError):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(NotFoundError)
    async def not_found_handler(_: Request, exc: NotFoundError):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(UnauthorizedError)
    async def unauthorized_handler(_: Request, exc: UnauthorizedError):
        return JSONResponse(status_code=401, content={"detail": str(exc)})

    @app.exception_handler(ForbiddenError)
    async def forbidden_handler(_: Request, exc: ForbiddenError):
        return JSONResponse(status_code=403, content={"detail": str(exc)})

    @app.exception_handler(ValidationError)
    async def validation_handler(_: Request, exc: ValidationError):
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(Exception)
    async def unhandled(_: Request, exc: Exception):
        # In production you would log the full stack trace here.
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

