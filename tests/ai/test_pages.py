# Copyright 2026
# ruff: noqa: D103,INP001
"""Tests for deterministic accepted AI handbook page boundaries."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import pytest
from pydantic import ValidationError

from scripts.ai.errors import AIAgentError, ErrorCode
from scripts.ai.manifest import load_sources
from scripts.ai.pages import (
    AcceptedPage,
    parse_accepted_page,
    render_chinese_page,
    render_english_page,
    validate_candidate,
)
from scripts.ai.types import NormalizedPage, Source, SourceManifest

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = load_sources(ROOT / "source-ai" / "sources.yaml")
WARNING = "本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。"  # noqa: RUF001


def _normalized(source: Source) -> NormalizedPage:
    """Build one short, deterministic normalized page."""
    markdown = f"# {source.title}\n\nShort source prose.\n"
    return NormalizedPage(
        source=source,
        markdown=markdown,
        content_sha256=sha256(markdown.encode("utf-8")).hexdigest(),
    )


def _translated(source: Source) -> str:
    """Build a short translated page with its required H1."""
    return f"# 中文 {source.slug}\n\n简短译文。\n"


def _write_candidate(root: Path, manifest: SourceManifest = MANIFEST) -> None:
    """Write exactly the ten paired synthetic pages below a managed root."""
    for source in manifest.root:
        normalized = _normalized(source)
        english_path = root / "en" / source.product / f"{source.slug}.md"
        chinese_path = root / "zh-CN" / source.product / f"{source.slug}.md"
        english_path.parent.mkdir(parents=True, exist_ok=True)
        chinese_path.parent.mkdir(parents=True, exist_ok=True)
        _ = english_path.write_bytes(render_english_page(normalized))
        _ = chinese_path.write_bytes(render_chinese_page(normalized, _translated(source)))


def _write_learning(root: Path, manifest: SourceManifest = MANIFEST) -> None:
    """Write the two read-only Chinese learning pages with exact routes."""
    for product in ("claude-code", "codex"):
        sources = [source for source in manifest.root if source.product == product]
        routes = "\n".join(
            f"- [页面](/ai/zh-CN/{source.product}/{source.slug})" for source in sources
        )
        path = root / "zh-CN" / f"{product}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        _ = path.write_text(f"# 学习路径\n\n{routes}\n", encoding="utf-8", newline="\n")


def _expect_invalid(managed_root: Path, learning_root: Path) -> None:
    """Assert one public validation boundary failure."""
    with pytest.raises(AIAgentError) as exc_info:
        validate_candidate(
            managed_root=managed_root,
            learning_root=learning_root,
            manifest=MANIFEST,
        )
    assert exc_info.value.code == ErrorCode.VALIDATION_FAILED  # noqa: S101


def _symlink_or_skip(link: Path, target: Path) -> None:
    """Create a symlink, or skip when the current platform denies it."""
    try:
        link.symlink_to(target)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"symlink unavailable: {exc}")


def _complete_roots(tmp_path: Path) -> tuple[Path, Path]:
    """Create a valid managed candidate and separate live learning root."""
    managed_root = tmp_path / "candidate"
    learning_root = tmp_path / "live-learn"
    _write_candidate(managed_root)
    _write_learning(learning_root)
    return managed_root, learning_root


def test_render_round_trip_has_exact_frontmatter_order_and_lf(tmp_path: Path) -> None:
    """Given a normalized page, render and parse the deterministic English bytes."""
    source = MANIFEST.root[0]
    payload = render_english_page(_normalized(source))
    path = tmp_path / "page.md"
    _ = path.write_bytes(payload)

    page = parse_accepted_page(path)

    expected_names = (
        "title",
        "source_id",
        "product",
        "lang",
        "canonical_url",
        "owner",
        "content_sha256",
    )
    frontmatter = payload.decode("utf-8").split("---\n", 2)[1].splitlines()
    assert tuple(line.split(": ", 1)[0] for line in frontmatter) == expected_names  # noqa: S101
    assert page.title == source.title  # noqa: S101
    assert page.body.endswith("Short source prose.\n")  # noqa: S101
    assert b"\r" not in payload  # noqa: S101
    assert payload.endswith(b"\n")  # noqa: S101

    malformed = payload.replace(b"title:", b"source_title:", 1)
    _ = path.write_bytes(malformed)
    with pytest.raises(AIAgentError) as exc_info:
        _ = parse_accepted_page(path)
    assert exc_info.value.code == ErrorCode.VALIDATION_FAILED  # noqa: S101


def test_accepted_page_is_frozen_extra_forbid_and_language_legal() -> None:
    """Given page fields, reject extras and illegal language-specific metadata."""
    source = MANIFEST.root[0]
    fields = {
        "title": source.title,
        "source_id": source.id,
        "product": source.product,
        "lang": "en",
        "canonical_url": source.canonical_url,
        "owner": source.owner,
        "content_sha256": "a" * 64,
        "body": "body\n",
    }

    with pytest.raises(ValidationError):
        _ = AcceptedPage.model_validate({**fields, "unexpected": "field"})
    with pytest.raises(ValidationError):
        _ = AcceptedPage.model_validate({**fields, "lang": "fr"})
    with pytest.raises(ValidationError):
        _ = AcceptedPage.model_validate({**fields, "content_sha256": "bad"})

    page = AcceptedPage.model_validate(fields)
    with pytest.raises(ValidationError):
        page.title = "changed"


def test_chinese_render_has_warning_official_attribution_and_translated_title(
    tmp_path: Path,
) -> None:
    """Given a translated H1, Chinese rendering preserves required disclosure order."""
    source = MANIFEST.root[0]
    path = tmp_path / "page.md"
    _ = path.write_bytes(render_chinese_page(_normalized(source), _translated(source)))
    page = parse_accepted_page(path)

    assert page.title == f"中文 {source.slug}"  # noqa: S101
    assert page.translation_of == source.id  # noqa: S101
    assert page.translation_model == "k3"  # noqa: S101
    assert page.ai_translated is True  # noqa: S101
    prefix = f"{WARNING}\n\n[Official source]({source.canonical_url})\n\n"
    prefix += f"Content owner: {source.owner}\n\n"
    assert page.body.startswith(prefix)  # noqa: S101
    assert "endorsed" not in page.body.lower()  # noqa: S101


def test_chinese_render_records_supported_alternate_translation_model(tmp_path: Path) -> None:
    """Record GLM attribution without weakening accepted-page metadata."""
    source = MANIFEST.root[0]
    path = tmp_path / "page.md"
    _ = path.write_bytes(
        render_chinese_page(
            _normalized(source),
            _translated(source),
            translation_model="glm-5.2",
        )
    )

    assert parse_accepted_page(path).translation_model == "glm-5.2"  # noqa: S101


def test_chinese_render_rejects_missing_translated_h1() -> None:
    """Given translated text without an H1, rendering fails at the page boundary."""
    with pytest.raises(AIAgentError) as exc_info:
        _ = render_chinese_page(_normalized(MANIFEST.root[0]), "简短译文。\n")
    assert exc_info.value.code == ErrorCode.VALIDATION_FAILED  # noqa: S101


def test_validate_candidate_accepts_exact_pairs_and_preserves_learning_snapshot(
    tmp_path: Path,
) -> None:
    """Given exact paired managed pages and live learning pages, validate read-only input."""
    managed_root, learning_root = _complete_roots(tmp_path)
    before = tuple(
        sorted(
            (path.relative_to(learning_root), path.read_bytes())
            for path in learning_root.rglob("*")
            if path.is_file()
        )
    )

    validate_candidate(
        managed_root=managed_root,
        learning_root=learning_root,
        manifest=MANIFEST,
    )

    after = tuple(
        sorted(
            (path.relative_to(learning_root), path.read_bytes())
            for path in learning_root.rglob("*")
            if path.is_file()
        )
    )
    assert before == after  # noqa: S101


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "orphan",
        "extra",
        "misrouted",
        "duplicate_metadata",
        "managed_symlink",
        "learning_symlink",
        "managed_decoy_learn",
    ],
)
def test_validate_candidate_rejects_managed_pair_and_tree_violations(
    tmp_path: Path,
    mutation: str,
) -> None:
    """Given one malformed tree or pairing, validation fails with a safe code."""
    managed_root, learning_root = _complete_roots(tmp_path)
    source = MANIFEST.root[0]
    target = managed_root / "en" / source.product / f"{source.slug}.md"

    match mutation:
        case "missing":
            _ = target.unlink()
        case "orphan":
            _ = (managed_root / "zh-CN" / "codex" / "orphan.md").write_text("x\n", encoding="utf-8")
        case "extra":
            _ = (managed_root / "unexpected.txt").write_text("x\n", encoding="utf-8")
        case "misrouted":
            destination = managed_root / "en" / "codex" / f"{source.slug}.md"
            _ = target.rename(destination)
        case "duplicate_metadata":
            other = MANIFEST.root[1]
            duplicate = managed_root / "en" / other.product / f"{other.slug}.md"
            _ = duplicate.write_bytes(target.read_bytes())
        case "managed_symlink":
            _ = target.unlink()
            _symlink_or_skip(target, managed_root / "zh-CN" / source.product / f"{source.slug}.md")
        case "learning_symlink":
            learning = learning_root / "zh-CN" / "claude-code.md"
            learning.unlink()
            _symlink_or_skip(learning, learning_root / "zh-CN" / "codex.md")
        case "managed_decoy_learn":
            (managed_root / "learn").mkdir()
        case unreachable:
            pytest.fail(f"unexpected mutation {unreachable}")
    _expect_invalid(managed_root, learning_root)


def test_validate_candidate_rejects_learning_links_and_nonregular_entry(tmp_path: Path) -> None:
    """Given wrong learning links or a nonregular root entry, reject the supplied live root."""
    managed_root, learning_root = _complete_roots(tmp_path)
    path = learning_root / "zh-CN" / "codex.md"
    _ = path.write_text("# 学习路径\n\n- [页面](/ai/zh-CN/codex/cli)\n", encoding="utf-8")
    _expect_invalid(managed_root, learning_root)


def test_validate_candidate_accepts_live_root_learning_only_when_it_is_its_own_learning_root(
    tmp_path: Path,
) -> None:
    managed_root, learning_root = _complete_roots(tmp_path)
    live_root = tmp_path / "live"
    _ = managed_root.replace(live_root)
    _ = learning_root.replace(live_root / "learn")

    validate_candidate(
        managed_root=live_root,
        learning_root=live_root / "learn",
        manifest=MANIFEST,
    )

    target = live_root / "en" / "claude-code" / "quickstart.md"
    target.unlink()
    _symlink_or_skip(target, live_root / "zh-CN" / "claude-code" / "quickstart.md")
    _expect_invalid(live_root, live_root / "learn")


def test_validate_candidate_rejects_candidate_learn_tree_when_learning_is_external(
    tmp_path: Path,
) -> None:
    managed_root, learning_root = _complete_roots(tmp_path)
    _ = (managed_root / "learn").mkdir()

    _expect_invalid(managed_root, learning_root)

    _write_learning(learning_root)
    fifo = learning_root / "unexpected.fifo"
    fifo.touch()
    _expect_invalid(managed_root, learning_root)


def test_validate_candidate_rejects_pair_hashes_that_do_not_match_english_body(
    tmp_path: Path,
) -> None:
    """Reject matching pair metadata when it does not hash the English Markdown."""
    managed_root, learning_root = _complete_roots(tmp_path)
    source = MANIFEST.root[0]
    normalized = _normalized(source)
    for language in ("en", "zh-CN"):
        path = managed_root / language / source.product / f"{source.slug}.md"
        payload = path.read_bytes().replace(
            normalized.content_sha256.encode("ascii"),
            b"0" * 64,
            1,
        )
        _ = path.write_bytes(payload)

    _expect_invalid(managed_root, learning_root)


def test_validate_candidate_rejects_a_sixth_learning_link(tmp_path: Path) -> None:
    """Reject a learning page that links beyond its exact five managed routes."""
    managed_root, learning_root = _complete_roots(tmp_path)
    path = learning_root / "zh-CN" / "codex.md"
    _ = path.write_text(
        path.read_text(encoding="utf-8") + "\n[额外链接](/unrelated)\n",
        encoding="utf-8",
        newline="\n",
    )

    _expect_invalid(managed_root, learning_root)


@pytest.mark.parametrize(
    "claim",
    [
        "This mirror is endorsed by OpenAI.",
        "本站得到 Anthropic 官方背书。",
    ],
)
def test_validate_candidate_rejects_source_endorsement_claims(
    tmp_path: Path,
    claim: str,
) -> None:
    """Reject bounded English and Chinese claims of source endorsement."""
    managed_root, learning_root = _complete_roots(tmp_path)
    source = MANIFEST.root[0]
    path = managed_root / "zh-CN" / source.product / f"{source.slug}.md"
    _ = path.write_text(
        path.read_text(encoding="utf-8") + f"\n{claim}\n",
        encoding="utf-8",
        newline="\n",
    )

    _expect_invalid(managed_root, learning_root)
