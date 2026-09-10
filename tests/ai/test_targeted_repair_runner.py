# Copyright 2026
# ruff: noqa: INP001, S101

"""Tests for the local exact-span targeted repair runner."""

from __future__ import annotations

import runpy
from collections import Counter
from pathlib import Path
from typing import Protocol, cast

import pytest


class _ApplyValidatedReplacements(Protocol):
    def __call__(  # noqa: PLR0913, PLR0917
        self,
        original: str,
        result: dict[str, object],
        issue_count: int,
        ignored_issue_indices: set[int] | None = None,
        expected_spans: list[str] | None = None,
        span_catalog: dict[str, tuple[int, str]] | None = None,
        required_contract: str | None = None,
        *,
        allow_legacy_contract: bool = False,
        allowed_link_issue_indices: set[int] | None = None,
    ) -> tuple[str, list[dict[str, object]]]: ...


class _LoadCachedResponse(Protocol):
    def __call__(self, path: Path) -> dict[str, object]: ...


class _InlineCodeTokens(Protocol):
    def __call__(self, markdown: str) -> Counter[str]: ...


class _LinkTargets(Protocol):
    def __call__(self, markdown: str) -> Counter[str]: ...


class _ProtectedMdxAttributes(Protocol):
    def __call__(self, markdown: str) -> Counter[tuple[str, str, str]]: ...


class _BuildRepairSpanCatalog(Protocol):
    def __call__(
        self,
        issues: list[dict[str, str]],
    ) -> dict[str, tuple[int, str]]: ...


class _ValidateDocumentInvariants(Protocol):
    def __call__(  # noqa: PLR0913
        self,
        original: str,
        revised: str,
        *,
        allowed_removed_link_targets: Counter[str] | None = None,
        allowed_added_link_targets: Counter[str] | None = None,
        allowed_removed_mdx_attributes: Counter[tuple[str, str, str]] | None = None,
        allowed_added_mdx_attributes: Counter[tuple[str, str, str]] | None = None,
    ) -> None: ...


def _runner_namespace() -> dict[str, object]:
    root = Path(__file__).resolve().parents[2]
    return runpy.run_path(
        str(root / ".ai-local" / "targeted-review-fix.py")
    )


def _runner_function() -> _ApplyValidatedReplacements:
    namespace = _runner_namespace()
    return cast(
        "_ApplyValidatedReplacements",
        namespace["apply_validated_replacements"],
    )


def _document_invariant_function() -> _ValidateDocumentInvariants:
    namespace = _runner_namespace()
    return cast(
        "_ValidateDocumentInvariants",
        namespace["validate_document_invariants"],
    )


def _result(old: str, new: str) -> dict[str, object]:
    return {
        "replacements": [
            {
                "old": old,
                "new": new,
                "issue_indices": [0],
            }
        ],
        "self_check": {"all_issues_addressed": True},
    }


def test_unique_subspan_inside_frozen_issue_is_accepted() -> None:
    """A provider may safely narrow one replacement inside its frozen span."""
    original = "# 标题\n\n前缀。错误片段。后缀。\n"

    revised, replacements = _runner_function()(
        original,
        _result("错误片段。", "正确片段。"),
        1,
        expected_spans=["前缀。错误片段。后缀。"],
    )

    assert revised == "# 标题\n\n前缀。正确片段。后缀。\n"
    assert len(replacements) == 1


def test_reader_facing_fence_content_may_change() -> None:
    """Text fences can carry reader-visible translation corrections."""
    original = "```text\nold reader-facing prose\n```\n"
    revised = "```text\nnew reader-facing prose\n```\n"

    _document_invariant_function()(original, revised)


def test_executable_fence_content_may_not_change() -> None:
    """Executable snippets remain byte-for-byte frozen."""
    original = "```python\nprint('old')\n```\n"
    revised = "```python\nprint('new')\n```\n"

    with pytest.raises(RuntimeError, match="Executable fenced code changed"):
        _document_invariant_function()(original, revised)


def test_reader_facing_fence_marker_may_not_change() -> None:
    """The prose exception never permits fence-language mutation."""
    original = "```text\nreader-facing prose\n```\n"
    revised = "```markdown\nreader-facing prose\n```\n"

    with pytest.raises(
        RuntimeError,
        match="Fenced block marker or language changed",
    ):
        _document_invariant_function()(original, revised)


def test_subspan_outside_frozen_issue_is_rejected() -> None:
    """An unrelated exact page span cannot claim coverage for the issue."""
    original = "# 标题\n\n冻结问题。另一个错误。\n"

    with pytest.raises(RuntimeError, match="unique exact subspan"):
        _ = _runner_function()(
            original,
            _result("另一个错误。", "另一个修复。"),
            1,
            expected_spans=["冻结问题。"],
        )


def test_span_id_contract_uses_local_immutable_old_text() -> None:
    """The provider supplies only an id and new text; local code owns old."""
    namespace = _runner_namespace()
    build_catalog = cast(
        "_BuildRepairSpanCatalog",
        namespace["build_repair_span_catalog"],
    )
    issues = [{"chinese_excerpt": "错误片段。"}]
    catalog = build_catalog(issues)
    span_id = next(iter(catalog))
    original = "# 标题\n\n错误片段。\n"
    result: dict[str, object] = {
        "replacements": [{"span_id": span_id, "new": "正确片段。"}],
        "self_check": {"all_issues_addressed": True},
    }

    revised, replacements = _runner_function()(
        original,
        result,
        1,
        expected_spans=["错误片段。"],
        span_catalog=catalog,
    )

    assert revised == "# 标题\n\n正确片段。\n"
    assert replacements[0]["old_sha256"]
    assert replacements[0]["issue_indices"] == [0]


def test_span_id_contract_rejects_provider_supplied_old_text() -> None:
    """A provider cannot override the immutable local old span."""
    namespace = _runner_namespace()
    build_catalog = cast(
        "_BuildRepairSpanCatalog",
        namespace["build_repair_span_catalog"],
    )
    catalog = build_catalog([{"chinese_excerpt": "错误片段。"}])
    span_id = next(iter(catalog))
    result: dict[str, object] = {
        "replacements": [
            {
                "span_id": span_id,
                "old": "另一个片段。",
                "new": "正确片段。",
            }
        ],
        "self_check": {"all_issues_addressed": True},
    }

    with pytest.raises(RuntimeError, match="must not return old"):
        _ = _runner_function()(
            "# 标题\n\n错误片段。\n",
            result,
            1,
            expected_spans=["错误片段。"],
            span_catalog=catalog,
        )


def test_live_strict_contract_rejects_legacy_old_new_fallback() -> None:
    """A strict live response cannot silently fall back to the legacy shape."""
    namespace = _runner_namespace()
    build_catalog = cast(
        "_BuildRepairSpanCatalog",
        namespace["build_repair_span_catalog"],
    )
    catalog = build_catalog([{"chinese_excerpt": "错误片段。"}])

    with pytest.raises(RuntimeError, match="requires span_id"):
        _ = _runner_function()(
            "# 标题\n\n错误片段。\n",
            _result("错误片段。", "正确片段。"),
            1,
            expected_spans=["错误片段。"],
            span_catalog=catalog,
            required_contract="span-id-v1",
        )


def test_legacy_cached_old_new_contract_remains_replayable() -> None:
    """Old immutable caches remain usable after the span-id migration."""
    original = "# 标题\n\n错误片段。\n"
    catalog = {"span-0000-deadbeefdeadbeef": (0, "错误片段。")}

    revised, _ = _runner_function()(
        original,
        _result("错误片段。", "正确片段。"),
        1,
        expected_spans=["错误片段。"],
        span_catalog=catalog,
        required_contract="span-id-v1",
        allow_legacy_contract=True,
    )

    assert revised == "# 标题\n\n正确片段。\n"


def test_repeated_page_subspan_is_rejected_before_frozen_check() -> None:
    """A repeated phrase remains unsafe even within the reviewed region."""
    original = "# 标题\n\n错误。前缀错误。后缀。\n"

    with pytest.raises(RuntimeError, match="occurs 2 times"):
        _ = _runner_function()(
            original,
            _result("错误。", "修复。"),
            1,
            expected_spans=["前缀错误。后缀。"],
        )


def test_replacement_cannot_introduce_a_nested_markdown_link() -> None:
    """A label-only frozen span cannot grow its own duplicate link target."""
    original = (
        "# 标题\n\n"
        "[安装 Claude Code 至开发容器](#add-claude-code-to-your-dev-container)\n"
    )

    with pytest.raises(RuntimeError, match="Markdown structural token counts"):
        _ = _runner_function()(
            original,
            _result(
                "[安装 Claude Code 至开发容器]",
                (
                    "[在开发容器中安装 Claude Code]"
                    "(#add-claude-code-to-your-dev-container)"
                ),
            ),
            1,
            expected_spans=["[安装 Claude Code 至开发容器]"],
        )


def test_complete_link_replacement_preserves_structural_tokens() -> None:
    """A full link may change its label while retaining its one target."""
    original = (
        "# 标题\n\n"
        "[安装 Claude Code 至开发容器](#add-claude-code-to-your-dev-container)\n"
    )
    old = (
        "[安装 Claude Code 至开发容器](#add-claude-code-to-your-dev-container)"
    )
    new = (
        "[在开发容器中安装 Claude Code](#add-claude-code-to-your-dev-container)"
    )

    revised, _ = _runner_function()(
        original,
        _result(old, new),
        1,
        expected_spans=[old],
    )

    assert new in revised


def test_soft_line_break_in_link_label_preserves_target() -> None:
    """A Markdown soft break in link text does not create a new target."""
    targets = cast("_LinkTargets", _runner_namespace()["link_targets"])

    assert targets("[Fix and verify\na finding](https://example.test/fix)\n") == targets(
        "[Fix and verify a finding](https://example.test/fix)\n"
    )


def test_authorized_mdx_href_value_change_is_bounded() -> None:
    """An authorized repair may change only an existing href value."""
    old = '<A href="/old">Learn more</A>'
    new = '<A href="/new">Learn more</A>'
    revised, _ = _runner_function()(
        f"{old}\n",
        _result(old, new),
        1,
        expected_spans=[old],
        allowed_link_issue_indices={0},
    )
    attributes = cast(
        "_ProtectedMdxAttributes",
        _runner_namespace()["protected_mdx_attributes"],
    )
    removed = attributes(old) - attributes(new)
    added = attributes(new) - attributes(old)

    _document_invariant_function()(
        f"{old}\n",
        revised,
        allowed_removed_mdx_attributes=removed,
        allowed_added_mdx_attributes=added,
    )


def test_authorized_link_issue_cannot_change_non_href_mdx_attribute() -> None:
    """Link authorization never permits unrelated MDX property changes."""
    old = '<A class="old">Learn more</A>'
    new = '<A class="new">Learn more</A>'

    with pytest.raises(RuntimeError, match="protected MDX attribute shape"):
        _ = _runner_function()(
            f"{old}\n",
            _result(old, new),
            1,
            expected_spans=[old],
            allowed_link_issue_indices={0},
        )


def test_inline_triple_backticks_are_not_a_fence_marker() -> None:
    """Inline documentation of a fence token remains repairable prose."""
    old = "Use the inline literal ` ```! ` in this sentence."
    new = "Keep the inline literal ` ```! ` in this sentence."

    revised, _ = _runner_function()(
        f"{old}\n",
        _result(old, new),
        1,
        expected_spans=[old],
    )

    assert revised == f"{new}\n"


def test_explicit_cache_loader_requires_versioned_result(
    tmp_path: Path,
) -> None:
    """A resumed provider response remains an explicit immutable envelope."""
    cache_path = tmp_path / "response.json"
    _ = cache_path.write_text(
        '{"version":1,"result":{"replacements":[]}}',
        encoding="utf-8",
        newline="\n",
    )
    loader = cast(
        "_LoadCachedResponse",
        _runner_namespace()["load_cached_response"],
    )

    assert loader(cache_path) == {"replacements": []}


def test_escaped_backtick_in_bold_shortcut_is_not_inline_code() -> None:
    """A literal shortcut backtick must not consume later code spans."""
    tokens = cast(
        "_InlineCodeTokens",
        _runner_namespace()["inline_code_tokens"],
    )
    before = (
        "Press **Ctrl+\\`** on Windows, then run `npm test` or "
        "`git status`."
    )
    after = (
        "在 Windows 上按 **Ctrl+\\`**, 然后运行 `npm test` 或 "
        "`git status`."
    )
    expected = Counter({"npm test": 1, "git status": 1})

    assert tokens(before) == expected
    assert tokens(after) == expected
