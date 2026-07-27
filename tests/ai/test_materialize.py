# Copyright 2026
# ruff: noqa: EM101,INP001,S101,TRY003

"""Private accepted-content materialization tests."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from scripts.ai.errors import AIAgentError, ErrorCode
from scripts.ai.manifest import load_sources
from scripts.ai.materialize import MaterializeOptions, materialize_ai
from tests.ai.fixture_support import install_content, normalized_pages

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "source-ai" / "sources.yaml"


def _options(tmp_path: Path, content_root: Path) -> MaterializeOptions:
    repo = tmp_path / "repo"
    repo.mkdir(exist_ok=True)
    return MaterializeOptions(
        repo_root=repo,
        content_root=content_root,
        docs_ai_root=repo / "docs" / "ai",
        manifest_path=MANIFEST_PATH,
    )


def _frontmatter_and_body(data: bytes) -> tuple[tuple[str, ...], bytes]:
    closing = data.index(b"\n---\n", len(b"---\n"))
    fields = tuple(data[len(b"---\n") : closing].decode("utf-8").splitlines())
    return fields, data[closing + len(b"\n---\n") :]


@pytest.mark.parametrize("kind", ["missing", "tracked_docs"])
def test_materialize_rejects_missing_or_nonprivate_content_root(
    tmp_path: Path,
    kind: str,
) -> None:
    """Given an invalid accepted root, when materialized, then validation fails."""
    # Given
    options = _options(tmp_path, tmp_path / "missing")
    if kind == "tracked_docs":
        options = MaterializeOptions(
            repo_root=REPO_ROOT,
            content_root=REPO_ROOT / "docs",
            docs_ai_root=tmp_path / "derived",
            manifest_path=MANIFEST_PATH,
        )

    # When / Then
    with pytest.raises(AIAgentError) as exc_info:
        _ = materialize_ai(options)
    assert exc_info.value.code == ErrorCode.VALIDATION_FAILED


def test_materialize_derives_exact_routes_and_preserves_accepted_content(
    tmp_path: Path,
) -> None:
    """Given 22 accepted pages, when derived, then routes and byte contracts are exact."""
    # Given
    manifest = load_sources(MANIFEST_PATH)
    content = tmp_path / "private"
    install_content(content, normalized_pages(manifest))
    options = _options(tmp_path, content)
    accepted_source_bytes = {
        (lang, source.id): (content / lang / source.product / f"{source.slug}.md").read_bytes()
        for source in manifest.root
        for lang in ("en", "zh-CN")
    }
    learning_bytes = {
        product: (content / "learn" / "zh-CN" / f"{product}.md").read_bytes()
        for product in ("claude-code", "codex")
    }

    # When
    routes = materialize_ai(options)

    # Then
    assert len(routes) == len(manifest.root) * 2 + 2
    assert {route.route for route in routes} == {
        *{
            f"/ai/{lang}/{source.product}/{source.slug}"
            for source in manifest.root
            for lang in ("en", "zh-CN")
        },
        "/ai/zh-CN/learn/claude-code",
        "/ai/zh-CN/learn/codex",
    }
    by_route = {route.route: route for route in routes}
    for source in manifest.root:
        en_route = f"/ai/en/{source.product}/{source.slug}"
        zh_route = f"/ai/zh-CN/{source.product}/{source.slug}"
        assert by_route[en_route].counterpart == zh_route
        assert by_route[zh_route].counterpart == en_route
        assert by_route[en_route].source_id == source.id
        assert by_route[zh_route].source_id == source.id
        for lang, prefix, label, counterpart in (
            ("en", "EN · ", "EN", zh_route),
            ("zh-CN", "中文 · ", "中文", en_route),
        ):
            original = accepted_source_bytes[(lang, source.id)]
            derived = (
                options.docs_ai_root / lang / source.product / f"{source.slug}.md"
            ).read_bytes()
            original_fields, original_body = _frontmatter_and_body(original)
            derived_fields, derived_body = _frontmatter_and_body(derived)
            assert derived_body == original_body
            assert (
                derived_fields[0] == f"title: {prefix}{original_fields[0].removeprefix('title: ')}"
            )
            assert set(derived_fields[1:]) == {
                *original_fields[1:],
                f"ai_counterpart: {counterpart}",
                f"ai_search_label: {label}",
            }
    for product in ("claude-code", "codex"):
        route = by_route[f"/ai/zh-CN/learn/{product}"]
        assert route.source_id is None
        assert route.lang == "zh-CN"
        assert route.counterpart is None
        assert (
            options.docs_ai_root / "zh-CN" / "learn" / f"{product}.md"
        ).read_bytes() == learning_bytes[product]
    assert not tuple(options.docs_ai_root.parent.glob(".ai-backup-*"))
    assert not tuple((options.repo_root / ".ai-local").glob(".ai-retired-*"))


def test_materialize_publishes_all_english_and_only_available_chinese(
    tmp_path: Path,
) -> None:
    """Keep existing Chinese pages live while a larger English set is reviewed."""
    manifest = load_sources(MANIFEST_PATH)
    content = tmp_path / "private"
    pages = normalized_pages(manifest)
    install_content(content, pages)
    missing = manifest.root[-1]
    (content / "zh-CN" / missing.product / f"{missing.slug}.md").unlink()
    for product in ("claude-code", "codex"):
        routes = "\n".join(
            f"- [Page](/ai/zh-CN/{page.source.product}/{page.source.slug})"
            for page in pages
            if page.source.product == product and page.source.id != missing.id
        )
        _ = (content / "learn" / "zh-CN" / f"{product}.md").write_text(
            f"# Learning\n\n{routes}\n",
            encoding="utf-8",
            newline="\n",
        )
    options = _options(tmp_path, content)

    routes = materialize_ai(options)
    by_route = {route.route: route for route in routes}
    missing_en = f"/ai/en/{missing.product}/{missing.slug}"
    missing_zh = f"/ai/zh-CN/{missing.product}/{missing.slug}"

    assert len(routes) == len(manifest.root) * 2 + 1
    assert missing_en in by_route
    assert by_route[missing_en].counterpart is None
    assert missing_zh not in by_route
    assert not (
        options.docs_ai_root / "zh-CN" / missing.product / f"{missing.slug}.md"
    ).exists()


def test_fixture_learning_paths_are_readable_spec_examples(tmp_path: Path) -> None:
    """Keep synthetic learning fixtures representative and readable."""
    manifest = load_sources(MANIFEST_PATH)
    content = tmp_path / "private"
    install_content(content, normalized_pages(manifest))

    for product in ("claude-code", "codex"):
        text = (content / "learn" / "zh-CN" / f"{product}.md").read_text(encoding="utf-8")
        assert text.startswith("# ")
        assert "适合谁阅读：" in text  # noqa: RUF001
        assert "## 推荐阅读顺序" in text
        expected = sum(source.product == product for source in manifest.root)
        assert text.count("学习目标：") == expected  # noqa: RUF001
        assert "遇到歧义时，请切换到对应英文页核对。" in text  # noqa: RUF001


def test_materialize_keeps_previous_tree_when_copy_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Given a live derived tree, when staging copy fails, then the live bytes survive."""
    # Given
    manifest = load_sources(MANIFEST_PATH)
    content = tmp_path / "private"
    install_content(content, normalized_pages(manifest))
    options = _options(tmp_path, content)
    sentinel = options.docs_ai_root / "sentinel.md"
    sentinel.parent.mkdir(parents=True)
    _ = sentinel.write_bytes(b"previous\n")

    def fail_copy(source: Path, destination: Path) -> None:
        del source, destination
        raise OSError("controlled copy failure")

    monkeypatch.setattr(shutil, "copy2", fail_copy)

    # When / Then
    with pytest.raises(AIAgentError) as exc_info:
        _ = materialize_ai(options)
    assert exc_info.value.code == ErrorCode.WRITE_FAILED
    assert sentinel.read_bytes() == b"previous\n"


def test_materialize_keeps_promoted_tree_when_retired_backup_cleanup_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Given cleanup partially fails after promotion, then the complete new tree stays live."""
    # Given
    manifest = load_sources(MANIFEST_PATH)
    content = tmp_path / "private"
    install_content(content, normalized_pages(manifest))
    options = _options(tmp_path, content)
    sentinel = options.docs_ai_root / "sentinel.md"
    sentinel.parent.mkdir(parents=True)
    _ = sentinel.write_bytes(b"previous\n")
    real_rmtree = shutil.rmtree
    cleanup_failed = False

    def fail_retired_cleanup(path: Path) -> None:
        nonlocal cleanup_failed
        cleanup_path = Path(path)
        if not cleanup_failed and cleanup_path.name.startswith((".ai-backup-", ".ai-retired-")):
            cleanup_failed = True
            first_page = next(cleanup_path.rglob("*.md"))
            first_page.unlink()
            raise OSError("controlled retired-backup cleanup failure")
        real_rmtree(cleanup_path)

    monkeypatch.setattr(shutil, "rmtree", fail_retired_cleanup)

    # When
    with pytest.raises(AIAgentError) as exc_info:
        _ = materialize_ai(options)

    # Then
    assert exc_info.value.code == ErrorCode.WRITE_FAILED
    assert cleanup_failed
    assert not sentinel.exists()
    assert len(tuple(options.docs_ai_root.rglob("*.md"))) == len(manifest.root) * 2 + 2
    assert not tuple(options.docs_ai_root.parent.glob(".ai-backup-*"))
    retired = tuple((options.repo_root / ".ai-local").glob(".ai-retired-*"))
    assert len(retired) == 1
