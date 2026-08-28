"""
Main FastAPI Application Entry Point for SIH Prototype.
"""
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.api.routes import api_router
from backend.app.core.config import settings
from backend.app.core.errors import (
    AppException,
    app_exception_handler,
    generic_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from backend.app.core.logging import logger, setup_logging
from backend.app.database.session import init_db


def create_application() -> FastAPI:
    """
    Application factory initializing FastAPI, database, middleware, routers, and exception handlers.
    """
    setup_logging()
    logger.info("Initializing SIH Risk Prediction API Application...")

    # Initialize SQLite Database Tables
    try:
        init_db()
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

    application = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="SIH 2026 - Land Acquisition & Infrastructure Project Delay Risk Prediction System",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Configure CORS Middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register Centralized Error Handlers
    application.add_exception_handler(AppException, app_exception_handler)
    application.add_exception_handler(RequestValidationError, validation_exception_handler)
    application.add_exception_handler(StarletteHTTPException, http_exception_handler)
    application.add_exception_handler(Exception, generic_exception_handler)

    # Mount API Router
    application.include_router(api_router, prefix=settings.API_V1_STR)

    return application


app = create_application()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
