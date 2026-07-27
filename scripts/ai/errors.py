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


class TranslationFailureReason(StrEnum):
    """Secret-safe categories for translation adapter failures."""

    PROVIDER_REQUEST = "provider_request"
    PROVIDER_AUTH = "provider_auth"
    PROVIDER_PERMISSION = "provider_permission"
    PROVIDER_NOT_FOUND = "provider_not_found"
    PROVIDER_QUOTA = "provider_quota"
    PROVIDER_SERVER = "provider_server"
    TRANSPORT = "transport"
    RESPONSE_INVALID = "response_invalid"
    OUTPUT_INVALID = "output_invalid"
    OUTPUT_TOKEN_INVALID = "output_token_invalid"  # noqa: S105
    OUTPUT_TOKEN_MISSING = "output_token_missing"  # noqa: S105
    OUTPUT_TOKEN_UNEXPECTED = "output_token_unexpected"  # noqa: S105
    OUTPUT_TOKEN_REORDERED = "output_token_reordered"  # noqa: S105
    OUTPUT_STRUCTURE_INVALID = "output_structure_invalid"
    OUTPUT_LITERAL_INVALID = "output_literal_invalid"


class AIAgentError(Exception):
    """Small typed exception that carries a task code and optional source id."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        source_id: SourceId | None = None,
        reason: TranslationFailureReason | None = None,
    ) -> None:
        """Initialize an error with a stable code and optional source identity."""
        super().__init__(message)
        self.code: ErrorCode = code
        self.source_id: SourceId | None = source_id
        self.reason: TranslationFailureReason | None = reason
