# Copyright 2026

"""Candidate-tree validation for accepted bilingual pages."""

from __future__ import annotations

import re
from hashlib import sha256
from typing import TYPE_CHECKING, Final, NoReturn

from pydantic import ValidationError

from scripts.ai.errors import AIAgentError, ErrorCode
from scripts.ai.page_format import WARNING, AcceptedPage, first_h1, parse_accepted_page

if TYPE_CHECKING:
    from pathlib import Path

    from scripts.ai.types import Source, SourceId, SourceManifest

_PAGE_COUNT: Final = 10
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
    english: dict[SourceId, AcceptedPage] = {}
    chinese: dict[SourceId, AcceptedPage] = {}
    for language, destination in (("en", english), ("zh-CN", chinese)):
        language_root = root / language
        _require_directory(language_root)
        if {path.name for path in language_root.iterdir()} != {"claude-code", "codex"}:
            _fail()
        for source in manifest.root:
            product_root = language_root / source.product
            _require_directory(product_root)
            expected = {
                item.slug + ".md" for item in manifest.root if item.product == source.product
            }
            if {path.name for path in product_root.iterdir()} != expected:
                _fail(source.id)
            page_path = product_root / f"{source.slug}.md"
            _require_regular_file(page_path, source.id)
            page = parse_accepted_page(page_path)
            if page.source_id != source.id:
                _fail(source.id)
            if page.source_id in destination:
                _fail(page.source_id)
            destination[page.source_id] = page
    if len(english) != _PAGE_COUNT or len(chinese) != _PAGE_COUNT:
        _fail()
    return english, chinese


def _validate_pair(source: Source, english: AcceptedPage, chinese: AcceptedPage) -> None:
    common = ("source_id", "product", "canonical_url", "owner", "content_sha256")
    for name in common:
        if getattr(english, name) != getattr(chinese, name):
            _fail(source.id)
    if (
        english.source_id != source.id
        or english.product != source.product
        or english.canonical_url != source.canonical_url
        or english.owner != source.owner
        or english.title != source.title
        or english.lang != "en"
        or chinese.lang != "zh-CN"
        or chinese.translation_of != source.id
    ):
        _fail(source.id)
    attribution = f"[Official source]({source.canonical_url})\n\nContent owner: {source.owner}\n\n"
    english_prefix = attribution
    chinese_prefix = f"{WARNING}\n\n{attribution}"
    if not english.body.startswith(english_prefix) or not chinese.body.startswith(chinese_prefix):
        _fail(source.id)
    english_markdown = english.body.removeprefix(english_prefix)
    translated = chinese.body.removeprefix(chinese_prefix)
    endorsed = _ENDORSEMENT_RE.search(english.body + chinese.body)
    if (
        sha256(english_markdown.encode("utf-8")).hexdigest() != english.content_sha256
        or chinese.title != first_h1(translated)
        or endorsed
    ):
        _fail(source.id)


def _validate_learning(root: Path, manifest: SourceManifest) -> None:
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
        expected = tuple(
            f"/ai/zh-CN/{source.product}/{source.slug}"
            for source in manifest.root
            if source.product == product
        )
        if links != expected:
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
