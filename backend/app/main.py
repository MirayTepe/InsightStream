"""InsightStream FastAPI application factory."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.error_handlers import init_exception_handlers
from app.core.logging_config import configure_logging
from app.api.v1 import auth_routes, health_routes, pdf_routes, chat_routes


def get_cors_origins() -> list[str]:
    """Resolve CORS origins from settings or defaults."""
    if settings.backend_cors_origins:
        return [str(origin) for origin in settings.backend_cors_origins]
    return [
        "http://localhost",
        "http://127.0.0.1",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    configure_logging()
    yield
    # Cleanup (close connections, etc.) can go here


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.project_name,
        description="Enterprise RAG platform with PDF ingestion, vector search, and AI-powered chat",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API v1 routes
    app.include_router(auth_routes.router, prefix=settings.api_v1_prefix)
    app.include_router(health_routes.router, prefix=settings.api_v1_prefix)
    app.include_router(pdf_routes.router, prefix=settings.api_v1_prefix)
    app.include_router(chat_routes.router, prefix=settings.api_v1_prefix)

    init_exception_handlers(app)
    return app


app = create_app()
