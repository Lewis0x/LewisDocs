# Copyright 2026

"""Compatibility facade for accepted bilingual page operations."""

from scripts.ai.page_format import (
    AcceptedPage,
    parse_accepted_page,
    render_chinese_page,
    render_english_page,
)
from scripts.ai.page_validation import (
    validate_candidate,
    validate_english_candidate,
    validate_publishable_candidate,
)

__all__ = (
    "AcceptedPage",
    "parse_accepted_page",
    "render_chinese_page",
    "render_english_page",
    "validate_candidate",
    "validate_english_candidate",
    "validate_publishable_candidate",
)
