"""System API router — health and infrastructure checks."""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.db.schema import verify_core_schema
from app.db.supabase import check_supabase_connection

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/database-test")
async def database_test() -> JSONResponse:
    """Verify that the backend can communicate with Supabase."""
    result = await check_supabase_connection()

    if result["connected"]:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "database": "connected",
            },
        )

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "success": False,
            "database": "disconnected",
            "error": {
                "code": "SUPABASE_CONNECTION_FAILED",
                "message": str(result["message"]),
            },
        },
    )


@router.get("/schema-test")
async def schema_test() -> JSONResponse:
    """Verify that Phase 2 core database tables exist."""
    result = verify_core_schema()

    if result["success"]:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "schema": "ready",
                "tables": result["tables"],
            },
        )

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "success": False,
            "schema": "missing",
            "tables": result["tables"],
            "message": result["message"],
            "hint": "Run sql/001_core_schema.sql in Supabase SQL Editor or: python scripts/apply_core_schema.py",
        },
    )
