# Copyright 2026
# ruff: noqa: INP001

"""Tests for deterministic assigned-final-review evidence validation."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from scripts.ai.final_review_evidence import (
    FinalReviewEvidenceError,
    validate_final_review_issue_evidence,
)

if TYPE_CHECKING:
    from pathlib import Path


def _write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(value, encoding="utf-8", newline="\n")


def test_matching_issue_excerpts_are_accepted(tmp_path: Path) -> None:
    """Exact source and candidate evidence is sufficient for a normal issue."""
    source = tmp_path / "en.md"
    candidate = tmp_path / "zh.md"
    _write(source, "# Guide\n\nThe feature is enabled.\n")
    _write(candidate, "# 指南\n\n该功能被错误地描述为禁用。\n")

    validate_final_review_issue_evidence(
        source_path=source,
        candidate_path=candidate,
        issues=(
            {
                "category": "semantic_reversal",
                "source_excerpt": "The feature is enabled.",
                "chinese_excerpt": "该功能被错误地描述为禁用。",
            },
        ),
    )


def test_missing_section_claim_is_rejected_when_section_body_exists(
    tmp_path: Path,
) -> None:
    """A present non-empty localized section disproves a whole-section claim."""
    source = tmp_path / "en.md"
    candidate = tmp_path / "zh.md"
    _write(
        source,
        "# Guide\n\n## Next steps\n\nRead the deployment guide.\n",
    )
    _write(
        candidate,
        "# 指南\n\n## 后续步骤\n\n请阅读部署指南。\n",
    )

    with pytest.raises(
        FinalReviewEvidenceError,
        match="missing_section_claim_contradicted",
    ):
        validate_final_review_issue_evidence(
            source_path=source,
            candidate_path=candidate,
            issues=(
                {
                    "category": "missing_translation_content",
                    "english_excerpt": (
                        "## Next steps\n\nRead the deployment guide."
                    ),
                    "chinese_excerpt": "## 后续步骤",
                },
            ),
        )


def test_non_missing_issue_requires_exact_candidate_evidence(
    tmp_path: Path,
) -> None:
    """Semantic issues cannot enter the ledger without Chinese evidence."""
    source = tmp_path / "en.md"
    candidate = tmp_path / "zh.md"
    _write(source, "# Guide\n\nThe feature is enabled.\n")
    _write(candidate, "# 指南\n\n该功能已启用。\n")

    with pytest.raises(
        FinalReviewEvidenceError,
        match="candidate_excerpt_missing",
    ):
        validate_final_review_issue_evidence(
            source_path=source,
            candidate_path=candidate,
            issues=(
                {
                    "category": "semantic_reversal",
                    "source_excerpt": "The feature is enabled.",
                },
            ),
        )
