"""FastAPI application factory.

Creates and configures the FastAPI application with all routers,
static files, CORS middleware, and templates.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from dataviz.config import get_settings
from dataviz.logger import get_logger
from dataviz.routers import api, pages

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Application lifespan events for startup and shutdown."""
    settings = get_settings()
    logger.info(
        "Starting %s on %s:%d (debug=%s)",
        settings.app_name,
        settings.host,
        settings.port,
        settings.debug,
    )
    yield
    logger.info("Shutting down %s", settings.app_name)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    application = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS middleware for local development
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount static files
    application.mount(
        "/static",
        StaticFiles(directory=str(Path(__file__).resolve().parent / "static")),
        name="static",
    )

    # Include routers
    application.include_router(pages.router)
    application.include_router(api.router)

    return application


# Application instance for uvicorn
app = create_app()
