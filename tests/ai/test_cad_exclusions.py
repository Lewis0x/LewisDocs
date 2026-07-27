# Copyright 2026
# ruff: noqa: E501,INP001,RUF001,S101,TC002,TC003

"""CAD-last path exclusion regression tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts import link_citations, rewrite_links
from scripts.ai.cad_paths import iter_cad_markdown


def test_iter_cad_markdown_returns_sorted_regular_files_outside_top_level_ai(
    tmp_path: Path,
) -> None:
    """Given mixed docs, when enumerated, then only sorted regular CAD Markdown remains."""
    # Given
    docs = tmp_path / "docs"
    (docs / "platforms").mkdir(parents=True)
    (docs / "ai" / "en").mkdir(parents=True)
    (docs / "nested" / "ai").mkdir(parents=True)
    expected = (docs / "a.md", docs / "nested" / "ai" / "kept.md", docs / "platforms" / "z.md")
    for path in (*expected, docs / "ai" / "en" / "private.md"):
        _ = path.write_text("# page\n", encoding="utf-8")
    (docs / "directory.md").mkdir()
    _ = (docs / "note.txt").write_text("not markdown\n", encoding="utf-8")

    # When
    actual = iter_cad_markdown(docs)

    # Then
    assert actual == expected


def test_rewrite_and_citation_entrypoints_leave_ai_sentinel_byte_exact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Given a private sentinel, when both CAD passes run, then its bytes are unchanged."""
    # Given
    docs = tmp_path / "docs"
    docs.mkdir()
    _ = (docs / "cad.md").write_text(
        "# CAD\n\n[回链：1 §一]\n\n## 参考来源\n\n- [官方 1] Source https://example.test\n",
        encoding="utf-8",
    )
    sentinel = docs / "ai" / "en" / "sentinel.md"
    sentinel.parent.mkdir(parents=True)
    before = b"\x00private [\xe5\xae\x98\xe6\x96\xb9 1] [\xe5\x9b\x9e\xe9\x93\xbe\xef\xbc\x9a1 \xc2\xa7\xe4\xb8\x80]\n"
    _ = sentinel.write_bytes(before)
    monkeypatch.setattr(rewrite_links, "DOCS", docs)
    monkeypatch.setattr(link_citations, "DOCS", docs)

    # When
    rewrite_status = rewrite_links.main()
    citation_status = link_citations.main()

    # Then
    assert rewrite_status == 0
    assert citation_status == 0
    assert sentinel.read_bytes() == before
