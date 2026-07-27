# Copyright 2026

"""Error types for AI manifest, fetch, and sync operations."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scripts.ai.types import SourceId


class ErrorCode(StrEnum):
    """Canonical task-level error codes."""

    MANIFEST_INVALID = "MANIFEST_INVALID"
    FETCH_FAILED = "FETCH_FAILED"
    KEY_REQUIRED = "KEY_REQUIRED"
    TRANSLATION_FAILED = "TRANSLATION_FAILED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    WRITE_FAILED = "WRITE_FAILED"


class AIAgentError(Exception):
    """Small typed exception that carries a task code and optional source id."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        source_id: SourceId | None = None,
    ) -> None:
        """Initialize an error with a stable code and optional source identity."""
        super().__init__(message)
        self.code: ErrorCode = code
        self.source_id: SourceId | None = source_id
