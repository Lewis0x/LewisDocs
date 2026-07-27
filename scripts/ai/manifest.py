# Copyright 2026

"""Manifest loading contract for canonical source definitions."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

from pydantic import ValidationError

from scripts.ai.errors import AIAgentError, ErrorCode
from scripts.ai.types import SourceManifest


def load_sources(path: Path) -> SourceManifest:
    """Load and parse the frozen source manifest."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        message = "cannot load source manifest"
        raise AIAgentError(code=ErrorCode.MANIFEST_INVALID, message=message) from exc

    try:
        return SourceManifest.model_validate_json(text)
    except (ValidationError, ValueError, TypeError) as exc:
        message = "source manifest is invalid"
        raise AIAgentError(code=ErrorCode.MANIFEST_INVALID, message=message) from exc
