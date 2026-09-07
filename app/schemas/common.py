"""Shared API response helpers."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Structured error payload."""

    code: str
    message: str


class ErrorResponse(BaseModel):
    """Standard error response envelope."""

    success: bool = False
    error: ErrorDetail


class SuccessResponse(BaseModel, Generic[T]):
    """Standard success response envelope."""

    success: bool = True
    message: str | None = None
    data: T


class ListResponse(BaseModel, Generic[T]):
    """Standard list response envelope."""

    success: bool = True
    count: int
    data: list[T] = Field(default_factory=list)
