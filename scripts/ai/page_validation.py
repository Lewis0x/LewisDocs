# Copyright 2026

"""Candidate-tree validation for accepted bilingual pages."""

from __future__ import annotations

import re
from hashlib import sha256
from os import scandir
from pathlib import Path
from typing import TYPE_CHECKING, Final, NoReturn

from pydantic import ValidationError

from scripts.ai.errors import AIAgentError, ErrorCode
from scripts.ai.page_format import WARNING, AcceptedPage, first_h1, parse_accepted_page

if TYPE_CHECKING:
    from scripts.ai.types import Source, SourceId, SourceManifest

_MARKDOWN_LINK_RE: Final = re.compile(r"\]\(([^)\s]+)\)")
_EN_CLAIM_SUBJECT: Final = (
    r"(?:\b(?:this|our|the)\s+(?:mirror|site|translation|team)\b|\blewisdocs\b)"
)
_EN_CLAIM_VERBS: Final = (
    r"(?:endorsed|approved|authorized|backed|partnered|affiliated|collaborating)"
)
_EN_CLAIM_PREDICATE: Final = (
    f"(?:(?:official(?:ly)?\\s+)?{_EN_CLAIM_VERBS}|official\\s+partner(?:ship)?)\\b"
)
_ZH_CLAIM_SUBJECT: Final = r"(?:本站|本镜像|本译文|本翻译|LewisDocs|维护团队)"
_ZH_CLAIM_PREDICATE: Final = r"(?:官方)?(?:认可|批准|授权|背书|合作(?:伙伴)?)"
_EN_CLAIM: Final = f"{_EN_CLAIM_SUBJECT}[^\\n]{{0,80}}\\b{_EN_CLAIM_PREDICATE}"
_ZH_CLAIM: Final = f"{_ZH_CLAIM_SUBJECT}[^\\n]{{0,40}}{_ZH_CLAIM_PREDICATE}"
_ENDORSEMENT_RE: Final = re.compile(f"{_EN_CLAIM}|{_ZH_CLAIM}", re.IGNORECASE)


def validate_candidate(
    *,
    managed_root: Path,
    learning_root: Path,
    manifest: SourceManifest,
) -> None:
    """Validate exact managed pairs and the separately supplied read-only learning root."""
    try:
        english, chinese = _parse_managed_pages(
            managed_root,
            manifest,
            allow_learning=learning_root == managed_root / "learn",
        )
        for source in manifest.root:
            _validate_pair(source, english[source.id], chinese[source.id])
        _validate_learning(learning_root, manifest)
    except AIAgentError:
        raise
    except (OSError, UnicodeDecodeError, ValidationError, ValueError) as exc:
        _fail(cause=exc)


def validate_english_candidate(
    *,
    managed_root: Path,
    manifest: SourceManifest,
) -> None:
    """Validate an exact English preview while translated pages are pending."""
    try:
        _require_directory(managed_root)
        if {path.name for path in managed_root.iterdir()} != {"en", "learn"}:
            _fail()
        pages = _parse_language(
            managed_root / "en",
            manifest,
            language="en",
            exact=True,
        )
        for source in manifest.root:
            _validate_english(source, pages[source.id])
        if len(pages) != len(manifest.root):
            _fail()
    except AIAgentError:
        raise
    except (OSError, UnicodeDecodeError, ValidationError, ValueError) as exc:
        _fail(cause=exc)


def validate_publishable_candidate(
    *,
    managed_root: Path,
    manifest: SourceManifest,
) -> frozenset[SourceId]:
    """Validate exact English pages plus the currently available Chinese subset."""
    try:
        _require_directory(managed_root)
        expected_root = {"en", "learn"}
        chinese_root = managed_root / "zh-CN"
        if chinese_root.exists():
            expected_root.add("zh-CN")
        if {path.name for path in managed_root.iterdir()} != expected_root:
            _fail()

        english = _parse_language(
            managed_root / "en",
            manifest,
            language="en",
            exact=True,
        )
        for source in manifest.root:
            _validate_english(source, english[source.id])

        translated: frozenset[SourceId] = frozenset()
        if chinese_root.exists():
            chinese = _parse_language(
                chinese_root,
                manifest,
                language="zh-CN",
                exact=False,
            )
            by_id = {source.id: source for source in manifest.root}
            for source_id, page in chinese.items():
                _validate_pair(by_id[source_id], english[source_id], page)
            translated = frozenset(chinese)
            _validate_learning(managed_root / "learn", manifest, translated)
    except AIAgentError:
        raise
    except (OSError, UnicodeDecodeError, ValidationError, ValueError) as exc:
        _fail(cause=exc)
    return translated


def _parse_managed_pages(
    root: Path,
    manifest: SourceManifest,
    *,
    allow_learning: bool,
) -> tuple[dict[SourceId, AcceptedPage], dict[SourceId, AcceptedPage]]:
    _require_directory(root)
    expected_root = {"en", "zh-CN", "learn"} if allow_learning else {"en", "zh-CN"}
    if {path.name for path in root.iterdir()} != expected_root:
        _fail()
    english = _parse_language(root / "en", manifest, language="en", exact=True)
    chinese = _parse_language(root / "zh-CN", manifest, language="zh-CN", exact=True)
    if len(english) != len(manifest.root) or len(chinese) != len(manifest.root):
        _fail()
    return english, chinese


def _parse_language(
    language_root: Path,
    manifest: SourceManifest,
    *,
    language: str,
    exact: bool,
) -> dict[SourceId, AcceptedPage]:
    _require_directory(language_root)
    products = {source.product for source in manifest.root}
    if {path.name for path in language_root.iterdir()} != products:
        _fail()
    pages: dict[SourceId, AcceptedPage] = {}
    for product in products:
        product_root = language_root / product
        _require_directory(product_root)
        sources = {
            source.slug + ".md": source
            for source in manifest.root
            if source.product == product
        }
        entries, directories = _regular_tree(product_root)
        if (exact and entries.keys() != sources.keys()) or not entries.keys() <= sources.keys():
            _fail()
        expected_directories = {
            parent.as_posix()
            for name in entries
            for parent in Path(name).parents
            if parent != Path()
        }
        if directories != expected_directories:
            _fail()
        for name, path in entries.items():
            source = sources[name]
            _require_regular_file(path, source.id)
            page = parse_accepted_page(path)
            if (
                page.source_id != source.id
                or page.lang != language
                or page.source_id in pages
            ):
                _fail(source.id)
            pages[page.source_id] = page
    return pages


def _regular_tree(root: Path) -> tuple[dict[str, Path], set[str]]:
    files: dict[str, Path] = {}
    directories: set[str] = set()

    def visit(directory: Path) -> None:
        with scandir(directory) as entries:
            for entry in entries:
                path = Path(entry.path)
                relative = path.relative_to(root).as_posix()
                if entry.is_symlink():
                    _fail()
                if entry.is_dir(follow_symlinks=False):
                    directories.add(relative)
                    visit(path)
                elif entry.is_file(follow_symlinks=False):
                    files[relative] = path
                else:
                    _fail()

    visit(root)
    return files, directories


def _validate_pair(source: Source, english: AcceptedPage, chinese: AcceptedPage) -> None:
    _validate_english(source, english)
    common = ("source_id", "product", "canonical_url", "owner", "content_sha256")
    for name in common:
        if getattr(english, name) != getattr(chinese, name):
            _fail(source.id)
    if (
        english.source_id != source.id
        or english.product != source.product
        or english.canonical_url != source.canonical_url
        or english.owner != source.owner
        or chinese.lang != "zh-CN"
        or chinese.translation_of != source.id
    ):
        _fail(source.id)
    attribution = f"[Official source]({source.canonical_url})\n\nContent owner: {source.owner}\n\n"
    chinese_prefix = f"{WARNING}\n\n{attribution}"
    if not chinese.body.startswith(chinese_prefix):
        _fail(source.id)
    translated = chinese.body.removeprefix(chinese_prefix)
    if chinese.title != first_h1(translated) or _ENDORSEMENT_RE.search(chinese.body):
        _fail(source.id)


def _validate_english(source: Source, english: AcceptedPage) -> None:
    if (
        english.source_id != source.id
        or english.product != source.product
        or english.canonical_url != source.canonical_url
        or english.owner != source.owner
        or english.title != source.title
        or english.lang != "en"
    ):
        _fail(source.id)
    prefix = f"[Official source]({source.canonical_url})\n\nContent owner: {source.owner}\n\n"
    if not english.body.startswith(prefix):
        _fail(source.id)
    markdown = english.body.removeprefix(prefix)
    if (
        sha256(markdown.encode("utf-8")).hexdigest() != english.content_sha256
        or _ENDORSEMENT_RE.search(english.body)
    ):
        _fail(source.id)


def _validate_learning(
    root: Path,
    manifest: SourceManifest,
    translated: frozenset[SourceId] | None = None,
) -> None:
    _require_directory(root)
    if {path.name for path in root.iterdir()} != {"zh-CN"}:
        _fail()
    language_root = root / "zh-CN"
    _require_directory(language_root)
    if {path.name for path in language_root.iterdir()} != {"claude-code.md", "codex.md"}:
        _fail()
    for product in ("claude-code", "codex"):
        path = language_root / f"{product}.md"
        _require_regular_file(path)
        links = tuple(_MARKDOWN_LINK_RE.findall(path.read_text(encoding="utf-8")))
        allowed = tuple(
            f"/ai/zh-CN/{source.product}/{source.slug}"
            for source in manifest.root
            if source.product == product
            and (translated is None or source.id in translated)
        )
        if (
            not links
            or len(set(links)) != len(links)
            or any(link not in allowed for link in links)
            or tuple(sorted(links, key=allowed.index)) != links
        ):
            _fail()


def _require_directory(path: Path) -> None:
    if path.is_symlink() or not path.is_dir():
        _fail()


def _require_regular_file(path: Path, source_id: SourceId | None = None) -> None:
    if path.is_symlink() or not path.is_file():
        _fail(source_id)


def _fail(source_id: SourceId | None = None, cause: Exception | None = None) -> NoReturn:
    raise AIAgentError(
        code=ErrorCode.VALIDATION_FAILED,
        message="page validation failed",
        source_id=source_id,
    ) from cause
