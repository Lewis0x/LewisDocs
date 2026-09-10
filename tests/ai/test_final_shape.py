# Copyright 2026
# ruff: noqa: INP001, S101

"""Tests for deterministic final-site-shape gates."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from scripts.ai.final_shape import (
    FindingSide,
    inspect_final_shape_pair,
    require_final_shape_pair,
    validate_final_shape_evidence,
)

if TYPE_CHECKING:
    from pathlib import Path


def _write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(value, encoding="utf-8", newline="\n")


def test_valid_localized_pair_passes_deterministic_gate(tmp_path: Path) -> None:
    """Localized prose may differ while protected Markdown structure remains equal."""
    source = tmp_path / "en.md"
    candidate = tmp_path / "zh-CN.md"
    _write(
        source,
        """\
---
title: Example
---
# Example

- Open [settings](/ai/en/codex/settings).

| Mode | Value |
| --- | --- |
| Fast | `true` |

![Settings](https://example.test/settings.png)

```json
{"enabled": true}
```
""",
    )
    _write(
        candidate,
        """\
---
title: 示例
---
# 示例

- 打开[设置](/ai/zh-CN/codex/settings)。

| 模式 | 值 |
| --- | --- |
| 快速 | `true` |

![设置](https://example.test/settings.png)

```json
{"enabled": true}
```
""",
    )

    evidence = require_final_shape_pair("codex/example", source, candidate)

    assert evidence.passed is True
    assert evidence.findings == ()
    assert evidence.source.heading_levels == (1,)
    assert evidence.candidate.images == 1


def test_gate_rejects_materializer_image_attribute_corruption(
    tmp_path: Path,
) -> None:
    """The known HTML-image conversion defect must fail before LLM review."""
    source = tmp_path / "en.md"
    candidate = tmp_path / "zh-CN.md"
    _write(source, '# Example\n\n![](https://example.test/icon.png" alt=)\n')
    _write(candidate, '# 示例\n\n![](https://example.test/icon.png" alt=)\n')

    evidence = inspect_final_shape_pair("codex/example", source, candidate)

    assert evidence.passed is False
    assert {
        (finding.code, finding.side) for finding in evidence.findings
    } >= {
        ("malformed_image", FindingSide.SOURCE),
        ("malformed_image", FindingSide.CANDIDATE),
    }
    with pytest.raises(ValueError, match="malformed_image"):
        _ = require_final_shape_pair("codex/example", source, candidate)


def test_gate_rejects_top_level_mdx_body_rendered_as_code(tmp_path: Path) -> None:
    """Four-space prose left after stripping Step must not reach semantic review."""
    source = tmp_path / "en.md"
    candidate = tmp_path / "zh-CN.md"
    _write(
        source,
        "# Example\n\n    This instruction is ordinary prose, not source code.\n",
    )
    _write(
        candidate,
        "# 示例\n\n    这是一段普通说明文字且不应渲染为代码。\n",
    )

    evidence = inspect_final_shape_pair("codex/example", source, candidate)

    assert evidence.source.suspicious_indented_lines == (3,)
    assert evidence.candidate.suspicious_indented_lines == (3,)
    assert all(
        finding.code == "top_level_indented_code"
        for finding in evidence.findings
    )


def test_gate_allows_indented_list_continuation(tmp_path: Path) -> None:
    """Indented prose remains valid when it is structurally nested under a list."""
    source = tmp_path / "en.md"
    candidate = tmp_path / "zh-CN.md"
    _write(source, "# Example\n\n- Step\n\n    Continue this list item.\n")
    _write(candidate, "# 示例\n\n- 步骤\n\n    继续说明该列表项。\n")

    evidence = require_final_shape_pair("codex/example", source, candidate)

    assert evidence.source.suspicious_indented_lines == ()
    assert evidence.candidate.suspicious_indented_lines == ()


def test_gate_ignores_mdx_name_inside_code_after_escaped_backtick(
    tmp_path: Path,
) -> None:
    """An escaped shortcut backtick must not hide the following code span."""
    source = tmp_path / "en.md"
    candidate = tmp_path / "zh-CN.md"
    _write(
        source,
        "# Example\n\nPress **Ctrl+\\`** and inspect `<Card>`.\n",
    )
    _write(
        candidate,
        "# Example\n\nPress **Ctrl+\\`** and inspect `<Card>`.\n",
    )

    evidence = require_final_shape_pair("codex/example", source, candidate)

    assert evidence.source.residual_mdx_lines == ()
    assert evidence.candidate.residual_mdx_lines == ()


def test_gate_keeps_wrapped_content_inside_numbered_list(tmp_path: Path) -> None:
    """A three-space list continuation may itself contain a wrapped line."""
    source = tmp_path / "en.md"
    candidate = tmp_path / "zh-CN.md"
    _write(
        source,
        """\
# Example

1. Start
   Describe the task
         and keep this wrapped line in the list item.
""",
    )
    _write(
        candidate,
        """\
# 绀轰緥

1. 寮€濮?
   鎻忚堪浠诲姟
         骞朵繚鎸佽繖涓崲琛屽湪鍒楄〃椤逛腑銆?
""",
    )

    evidence = require_final_shape_pair("codex/example", source, candidate)

    assert evidence.source.suspicious_indented_lines == ()
    assert evidence.candidate.suspicious_indented_lines == ()


def test_gate_rejects_pair_structure_drift(tmp_path: Path) -> None:
    """Heading, link, image, table, and fence evidence is pairwise checked."""
    source = tmp_path / "en.md"
    candidate = tmp_path / "zh-CN.md"
    _write(
        source,
        "# Example\n\n## Setup\n\n[Open](/setup)\n\n```text\nvalue\n```\n",
    )
    _write(candidate, "# 示例\n\n[打开](/setup)\n")

    evidence = inspect_final_shape_pair("codex/example", source, candidate)
    codes = {finding.code for finding in evidence.findings}

    assert "heading_structure" in codes
    assert "fence_structure" in codes


def test_recomputed_evidence_rejects_changed_files(tmp_path: Path) -> None:
    """Stored evidence is bound to current bytes rather than trusted as metadata."""
    source = tmp_path / "en.md"
    candidate = tmp_path / "zh-CN.md"
    _write(source, "# Example\n")
    _write(candidate, "# 示例\n")
    evidence = require_final_shape_pair("codex/example", source, candidate)
    _write(candidate, "# 示例\n\n- 新增结构\n")

    with pytest.raises(ValueError, match="does not match"):
        validate_final_shape_evidence(evidence, source, candidate)
