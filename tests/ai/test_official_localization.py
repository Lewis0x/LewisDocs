# Copyright 2026
# ruff: noqa: D103,INP001,RUF001
"""Tests for owner-published Chinese localization validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.ai.manifest import load_sources
from scripts.ai.official_localization import (
    official_chinese_urls,
    validate_official_localization,
)

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = load_sources(ROOT / "source-ai" / "sources.yaml")


def _paired_markdown() -> tuple[str, str]:
    english = """# Configure Claude Code

Use this page to configure Claude Code for your team and keep the setup predictable.

## Install

- Run the command.
- Check the result.

```bash
claude --version
```

[Read more](/docs/en/overview)
"""
    chinese = """# 配置 Claude Code

使用本页为团队配置 Claude Code，并使设置过程保持清晰、稳定和可重复执行。

<h2 id="install">

安装

</h2>

- 运行命令并等待命令完成，然后检查终端中显示的结果是否符合预期。
- 检查最终结果，并确认团队中的其他成员也能够使用相同配置正常工作。

```bash
claude --version
```

[了解更多](/docs/zh-CN/overview)
"""
    return english, chinese


def test_official_chinese_urls_transform_manifest_urls_not_source_id() -> None:
    source = next(source for source in MANIFEST.root if source.id == "claude-code/extensions")

    canonical_url, fetch_url = official_chinese_urls(source)

    assert canonical_url.endswith("/docs/zh-CN/features-overview")  # noqa: S101
    assert fetch_url.endswith("/docs/zh-CN/features-overview.md")  # noqa: S101


def test_validate_official_localization_accepts_matching_current_bodies() -> None:
    english, chinese = _paired_markdown()

    validate_official_localization(english, chinese)


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_code",
        "changed_link_target",
        "changed_structure",
        "untranslated_prose",
    ],
)
def test_validate_official_localization_rejects_non_equivalent_bodies(
    mutation: str,
) -> None:
    english, chinese = _paired_markdown()
    match mutation:
        case "missing_code":
            chinese = chinese.replace("```bash\nclaude --version\n```\n", "")
        case "changed_link_target":
            chinese = chinese.replace("/docs/zh-CN/overview", "/docs/zh-CN/setup")
        case "changed_structure":
            chinese = chinese.replace('<h2 id="install">', '<h3 id="install">')
        case "untranslated_prose":
            chinese += (
                "\nThis paragraph is intentionally long enough to represent untranslated "
                "English prose that should not pass the official localization gate.\n"
            )
        case unreachable:
            pytest.fail(f"unexpected mutation {unreachable}")

    with pytest.raises(ValueError, match="official localization"):
        validate_official_localization(english, chinese)


def test_structure_mismatch_reports_the_differing_dimensions() -> None:
    english, chinese = _paired_markdown()
    chinese = chinese.replace("\n- ", "\n", 1)

    with pytest.raises(
        ValueError,
        match=r"Markdown structure differs: list_items en=2 zh-CN=1",
    ):
        validate_official_localization(english, chinese)
