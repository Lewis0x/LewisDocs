# Copyright 2026
# ruff: noqa: D103,INP001,S101

"""Tests for deterministic deep-audit preflight evidence."""

from __future__ import annotations

from typing import TYPE_CHECKING

from scripts.ai.audit_preflight import (
    AuditPreflightEvidence,
    PreflightSeverity,
    inspect_audit_preflight_pair,
)

if TYPE_CHECKING:
    from pathlib import Path

EXPECTED_BROKEN_FRAGMENT_COUNT = 2
EXPECTED_FENCE_LINE_START = 3


def _write(path: Path, content: str) -> None:
    _ = path.write_text(content, encoding="utf-8", newline="\n")


def _inspect(tmp_path: Path, source: str, candidate: str) -> AuditPreflightEvidence:
    source_path = tmp_path / "en.md"
    candidate_path = tmp_path / "zh-CN.md"
    _write(source_path, source)
    _write(candidate_path, candidate)
    return inspect_audit_preflight_pair("codex/example", source_path, candidate_path)


def test_detects_broken_visible_same_page_fragment_with_unique_span(tmp_path: Path) -> None:
    evidence = _inspect(
        tmp_path,
        "# Guide\n\n## Setup\n\nSee [setup](#setup).\n",
        "# 指南\n\n## 设置\n\n参见[设置](#missing-anchor)。\n",
    )

    finding = next(
        item for item in evidence.findings if item.code == "broken_same_page_fragment"
    )
    assert finding.severity is PreflightSeverity.HARD
    assert finding.candidate_span is not None
    assert finding.candidate_span.text == "[设置](#missing-anchor)"
    assert not evidence.hard_passed


def test_ignores_fragments_in_fenced_and_inline_code(tmp_path: Path) -> None:
    evidence = _inspect(
        tmp_path,
        "# Guide\n\n## Setup\n",
        "# 指南\n\n## 设置\n\n`[示例](#missing)`\n\n```md\n[示例](#missing)\n```\n",
    )

    assert "broken_same_page_fragment" not in {item.code for item in evidence.findings}
    assert evidence.hard_passed


def test_accepts_explicit_html_heading_fragment_outside_fences(tmp_path: Path) -> None:
    evidence = _inspect(
        tmp_path,
        '# Guide\n\n<h2 id="auto-mode">\n  Auto mode\n</h2>\n',
        '# 指南\n\n[自动模式](#auto-mode)\n\n<h2 class="mode" id="auto-mode">\n'
        "  自动模式\n"
        "</h2>\n",
    )

    assert "broken_same_page_fragment" not in {item.code for item in evidence.findings}
    assert "auto-mode" in evidence.candidate_heading_ids
    assert evidence.hard_passed


def test_duplicate_heading_slug_is_valid_and_unknown_slug_is_hard(tmp_path: Path) -> None:
    evidence = _inspect(
        tmp_path,
        "# Guide\n\n## Repeat\n\n## Repeat\n",
        "# 指南\n\n## 重复\n\n## 重复\n\n[第二节](#重复-1)\n[错误](#重复-2)\n",
    )

    broken = [item for item in evidence.findings if item.code == "broken_same_page_fragment"]
    assert len(broken) == 1
    assert "重复-2" in broken[0].message
    assert evidence.candidate_heading_ids == ("指南", "重复", "重复-1")


def test_multiple_broken_fragments_on_one_line_have_distinct_ids(
    tmp_path: Path,
) -> None:
    evidence = _inspect(
        tmp_path,
        "# Guide\n",
        "# 指南\n\n参见[第一项](#missing-one)和[第二项](#missing-two)。\n",
    )

    broken = [
        item
        for item in evidence.findings
        if item.code == "broken_same_page_fragment"
    ]
    assert len(broken) == EXPECTED_BROKEN_FRAGMENT_COUNT
    assert (
        len({item.finding_id for item in broken})
        == EXPECTED_BROKEN_FRAGMENT_COUNT
    )


def test_detects_heading_and_list_hierarchy_mismatch(tmp_path: Path) -> None:
    evidence = _inspect(
        tmp_path,
        "# Guide\n\n## Setup\n\n- First\n  - Nested\n",
        "# 指南\n\n### 设置\n\n1. 第一项\n- 嵌套项\n",
    )

    assert {item.code for item in evidence.findings} >= {
        "heading_hierarchy_mismatch",
        "list_hierarchy_mismatch",
    }
    assert all(
        item.severity is PreflightSeverity.HARD
        for item in evidence.findings
        if item.code.endswith("hierarchy_mismatch")
    )


def test_exact_candidate_span_preserves_indentation_and_trailing_spaces(
    tmp_path: Path,
) -> None:
    evidence = _inspect(
        tmp_path,
        "# Guide\n\n## Setup\n",
        "# 指南\n\n  ### 设置   \n",
    )

    finding = next(
        item for item in evidence.findings if item.code == "heading_hierarchy_mismatch"
    )
    assert finding.candidate_span is not None
    assert finding.candidate_span.text == "  ### 设置   "


def test_emits_candidate_hints_for_unique_marker_and_english_link_label(tmp_path: Path) -> None:
    evidence = _inspect(
        tmp_path,
        "# Guide\n\nRead [开始](/guide).\n",
        "# 指南\n\n阅读[Get started](/guide)。内容…\n",
    )

    findings = {item.code: item for item in evidence.findings}
    assert findings["candidate_only_truncation_marker"].severity is PreflightSeverity.CANDIDATE_HINT
    assert findings["visible_english_link_label"].candidate_span is not None
    assert findings["visible_english_link_label"].candidate_span.text == "[Get started](/guide)"
    assert evidence.hard_passed


def test_flags_long_identical_reader_fence_but_not_code_or_localized_copy(
    tmp_path: Path,
) -> None:
    source = (
        "# Guide\n\n"
        "```text theme={null}\n"
        "Subject: Claude Code is ready for your engineering team today\n\n"
        "Open the project, review the plan, and share feedback with everyone.\n"
        "```\n\n"
        "```python\n"
        "print('literal output stays unchanged')\n"
        "```\n"
    )
    unchanged = _inspect(
        tmp_path,
        source,
        source.replace("# Guide", "# 指南", 1),
    )

    finding = next(
        item
        for item in unchanged.findings
        if item.code == "identical_user_facing_fence"
    )
    assert finding.severity is PreflightSeverity.CANDIDATE_HINT
    assert finding.candidate_span is not None
    assert finding.candidate_span.line_start == EXPECTED_FENCE_LINE_START
    assert "Subject: Claude Code" in finding.candidate_span.text
    assert len(
        [
            item
            for item in unchanged.findings
            if item.code == "identical_user_facing_fence"
        ]
    ) == 1

    localized = _inspect(
        tmp_path,
        source,
        source.replace("# Guide", "# 指南", 1).replace(
            (
                "Subject: Claude Code is ready for your engineering team today\n\n"
                "Open the project, review the plan, and share feedback with everyone."
            ),
            "主题: Claude Code 已可供工程团队使用\n\n打开项目, 审阅计划, 并向团队反馈.",
        ),
    )
    assert "identical_user_facing_fence" not in {
        item.code for item in localized.findings
    }


def test_product_name_and_url_link_labels_are_not_hints(tmp_path: Path) -> None:
    evidence = _inspect(
        tmp_path,
        "# Guide\n",
        "# 指南\n\n[Codex](/codex) [https://example.test](https://example.test)\n",
    )

    assert "visible_english_link_label" not in {item.code for item in evidence.findings}


def test_preflight_evidence_and_finding_ids_are_deterministic(tmp_path: Path) -> None:
    source = "# Guide\n\n## Setup\n"
    candidate = "# 指南\n\n## 设置\n\n[错误](#missing)\n"
    first = _inspect(tmp_path, source, candidate)
    second = _inspect(tmp_path, source, candidate)

    assert first == second
    assert first.findings[0].finding_id == second.findings[0].finding_id
