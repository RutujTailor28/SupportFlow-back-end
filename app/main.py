"""FastAPI application entry point."""

import utils.session
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import analytics, knowledge_base, rules, system, tickets
from app.core.config import settings
from app.core.exceptions import AppError
from app.db.supabase import check_supabase_connection, init_supabase_clients


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Initialize services on startup."""
    init_supabase_clients()
    connection = await check_supabase_connection()
    if connection["connected"]:
        print("✓ Supabase connected successfully")
    elif connection["configured"]:
        print(f"✗ Supabase connection failed: {connection['message']}")
    else:
        print("⚠ Supabase not configured — add keys to backend/.env")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    """Return structured application errors."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "detail": exc.message,
            "error": {
                "code": exc.code,
                "message": exc.message,
            },
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    """Return structured validation errors."""
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "detail": "Validation error",
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request data",
                "fields": exc.errors(),
            },
        },
    )


app.include_router(system.router, prefix="/api/v1")
app.include_router(tickets.router, prefix="/api/v1")
app.include_router(knowledge_base.router, prefix="/api/v1")
app.include_router(rules.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint confirming the API is running."""
    return {"message": "SupportFlow API is running"}


@app.get("/health")
async def health() -> dict[str, str | bool]:
    """Health check endpoint."""
    return {
        "success": True,
        "status": "healthy",
        "service": "SupportFlow API",
    }
