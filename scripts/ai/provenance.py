# Copyright 2026

"""Deterministic translation provenance updates for reviewed candidates."""

from __future__ import annotations

import re
from typing import Final, Literal

TranslationModel = Literal["k3", "glm-5.2"]

_TRANSLATION_MODEL_LINE: Final = re.compile(
    r"(?m)^translation_model: (?P<model>[^\r\n]+)(?P<ending>\r?)$"
)


def stamp_translation_model(markdown: str, model: TranslationModel) -> str:
    """Set exactly one frontmatter translation model without touching prose."""
    matches = tuple(_TRANSLATION_MODEL_LINE.finditer(markdown))
    if len(matches) != 1:
        message = "candidate must contain exactly one translation_model field"
        raise ValueError(message)
    match = matches[0]
    frontmatter_end = _frontmatter_end(markdown)
    if match.start() >= frontmatter_end:
        message = "translation_model field is outside frontmatter"
        raise ValueError(message)
    if match.group("model") == model:
        return markdown
    return (
        markdown[: match.start("model")]
        + model
        + markdown[match.end("model") :]
    )


def _frontmatter_end(markdown: str) -> int:
    if not markdown.startswith("---\n") and not markdown.startswith("---\r\n"):
        message = "candidate has no YAML frontmatter"
        raise ValueError(message)
    match = re.search(r"(?:\r?\n)---(?:\r?\n)", markdown[3:])
    if match is None:
        message = "candidate has unclosed YAML frontmatter"
        raise ValueError(message)
    return 3 + match.end()
