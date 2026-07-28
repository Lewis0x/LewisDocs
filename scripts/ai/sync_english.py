# Copyright 2026

"""Fetch and atomically publish the complete English official-doc snapshot."""

from __future__ import annotations

import json
import re
import shutil
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from itertools import pairwise
from pathlib import Path
from typing import TYPE_CHECKING, Final, cast

from scripts.ai.errors import AIAgentError, ErrorCode
from scripts.ai.fetch import fetch_source
from scripts.ai.http_client import create_http_client
from scripts.ai.manifest import load_sources
from scripts.ai.normalize import normalize_source
from scripts.ai.page_format import WARNING
from scripts.ai.pages import (
    parse_accepted_page,
    render_chinese_page,
    render_english_page,
    validate_publishable_candidate,
)
from scripts.ai.types import NormalizedPage

if TYPE_CHECKING:
    import httpx2

    from scripts.ai.types import Source

_WORKERS: Final = 8
_FETCH_PASSES: Final = 4
_LEARNING_SECTION_RE: Final = re.compile(r"(?m)^##\s+\d+\.\s+")
_LEARNING_LINK_RE: Final = re.compile(r"\]\((/ai/zh-CN/[^)\s]+)\)")
_IMAGE_RE: Final = re.compile(r"!\[([^\]]*)]\([^)]+\)")
_LINK_RE: Final = re.compile(r"\[([^\]]+)]\([^)]+\)")
_AUTOLINK_RE: Final = re.compile(r"<https?://[^>]+>")
_PLAIN_URL_RE: Final = re.compile(r"https?://\S+")
_HTML_COMMENT_RE: Final = re.compile(r"(?s)<!--.*?-->")
_HTML_TAG_RE: Final = re.compile(r"</?[A-Za-z][^>]*>")
_BLOCK_MARKER_RE: Final = re.compile(r"(?m)^\s{0,3}(?:#{1,6}|[-+*>]|\d+[.)])\s*")
_INLINE_MARKER_RE: Final = re.compile(r"[*_~`]")
_WHITESPACE_RE: Final = re.compile(r"\s+")
_TYPOGRAPHY_TRANSLATION: Final = str.maketrans(
    {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u00a0": " ",
    }
)


def _source_fingerprint(source: Source) -> str:
    return sha256(source.model_dump_json().encode("utf-8")).hexdigest()


def _cache_path(cache_root: Path, source: Source) -> Path:
    return cache_root / source.product / f"{source.slug}.json"


def _read_cached_page(cache_root: Path, source: Source) -> NormalizedPage | None:
    try:
        payload = json.loads(_cache_path(cache_root, source).read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if (
        not isinstance(payload, dict)
        or payload.get("version") != 1
        or payload.get("source") != _source_fingerprint(source)
        or not isinstance(payload.get("markdown"), str)
    ):
        return None
    markdown = cast("str", payload["markdown"])
    return NormalizedPage(
        source=source,
        markdown=markdown,
        content_sha256=sha256(markdown.encode("utf-8")).hexdigest(),
    )


def _fetch_and_cache(
    client: httpx2.Client,
    cache_root: Path,
    source: Source,
) -> NormalizedPage | None:
    cached = _read_cached_page(cache_root, source)
    if cached is not None:
        return cached
    try:
        page = normalize_source(source=source, fetched=fetch_source(client, source))
    except AIAgentError:
        return None
    path = _cache_path(cache_root, source)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(
            {
                "version": 1,
                "source": _source_fingerprint(source),
                "markdown": page.markdown,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )
    temporary.replace(path)
    return page


def _fetch_all(
    cache_root: Path,
    sources: tuple[Source, ...],
) -> tuple[NormalizedPage, ...]:
    pages = {
        source.id: cached
        for source in sources
        if (cached := _read_cached_page(cache_root, source)) is not None
    }
    for attempt in range(_FETCH_PASSES):
        missing = tuple(source for source in sources if source.id not in pages)
        if not missing:
            break
        with (
            create_http_client() as client,
            ThreadPoolExecutor(max_workers=_WORKERS) as executor,
        ):
            fetched = executor.map(
                lambda source: _fetch_and_cache(client, cache_root, source),
                missing,
            )
            for source, page in zip(missing, fetched, strict=True):
                if page is not None:
                    pages[source.id] = page
        remaining = len(sources) - len(pages)
        _ = sys.stdout.write(
            f"English fetch pass {attempt + 1}: "
            f"{len(pages)}/{len(sources)} cached, {remaining} remaining\n"
        )
        if remaining:
            time.sleep(attempt + 1)
    missing = tuple(source for source in sources if source.id not in pages)
    if missing:
        raise AIAgentError(
            code=ErrorCode.FETCH_FAILED,
            message=f"{len(missing)} source pages could not be fetched",
            source_id=missing[0].id,
        )
    return tuple(pages[source.id] for source in sources)


def _semantic_content(markdown: str) -> str:
    text = markdown.translate(_TYPOGRAPHY_TRANSLATION)
    text = _HTML_COMMENT_RE.sub(" ", text)
    text = _IMAGE_RE.sub(r"\1", text)
    text = _LINK_RE.sub(r"\1", text)
    text = _AUTOLINK_RE.sub(" URL ", text)
    text = _PLAIN_URL_RE.sub(" URL ", text)
    text = _HTML_TAG_RE.sub(" ", text)
    text = _BLOCK_MARKER_RE.sub("", text)
    text = _INLINE_MARKER_RE.sub("", text)
    return _WHITESPACE_RE.sub(" ", text).strip()


def _preserved_translation(
    content: Path,
    page: NormalizedPage,
) -> bytes | None:
    english_path = content / "en" / page.source.product / f"{page.source.slug}.md"
    chinese_path = content / "zh-CN" / page.source.product / f"{page.source.slug}.md"
    try:
        english = parse_accepted_page(english_path)
        chinese = parse_accepted_page(chinese_path)
    except (AIAgentError, OSError, ValueError):
        return None
    metadata_matches = (
        english.source_id == page.source.id
        and chinese.source_id == page.source.id
        and english.content_sha256 == chinese.content_sha256
        and english.canonical_url == page.source.canonical_url
        and chinese.canonical_url == page.source.canonical_url
        and english.owner == page.source.owner
        and chinese.owner == page.source.owner
        and chinese.translation_of == page.source.id
    )
    if not metadata_matches or chinese.translation_model is None:
        return None
    english_prefix = (
        f"[Official source]({page.source.canonical_url})\n\n"
        f"Content owner: {page.source.owner}\n\n"
    )
    chinese_prefix = f"{WARNING}\n\n{english_prefix}"
    if not english.body.startswith(english_prefix) or not chinese.body.startswith(chinese_prefix):
        return None
    previous_markdown = english.body.removeprefix(english_prefix)
    if _semantic_content(previous_markdown) != _semantic_content(page.markdown):
        return None
    translated = chinese.body.removeprefix(chinese_prefix)
    return render_chinese_page(
        page,
        translated,
        translation_model=chinese.translation_model,
    )


def _populate_candidate(
    candidate: Path,
    content: Path,
    pages: tuple[NormalizedPage, ...],
) -> int:
    translated = 0
    translated_routes: set[str] = set()
    for page in pages:
        english = candidate / "en" / page.source.product / f"{page.source.slug}.md"
        english.parent.mkdir(parents=True, exist_ok=True)
        english.write_bytes(render_english_page(page))
        preserved = _preserved_translation(content, page)
        if preserved is None:
            continue
        chinese = candidate / "zh-CN" / page.source.product / f"{page.source.slug}.md"
        chinese.parent.mkdir(parents=True, exist_ok=True)
        chinese.write_bytes(preserved)
        translated += 1
        translated_routes.add(
            f"/ai/zh-CN/{page.source.product}/{page.source.slug}"
        )
    _copy_learning_paths(candidate, content, translated_routes)
    return translated


def _copy_learning_paths(
    candidate: Path,
    content: Path,
    translated_routes: set[str],
) -> None:
    learning = content / "learn" / "zh-CN"
    if not learning.is_dir() or learning.is_symlink():
        msg = "the accepted learning-path tree is missing"
        raise ValueError(msg)
    destination = candidate / "learn" / "zh-CN"
    destination.mkdir(parents=True)
    for product in ("claude-code", "codex"):
        source = learning / f"{product}.md"
        text = source.read_text(encoding="utf-8")
        starts = [match.start() for match in _LEARNING_SECTION_RE.finditer(text)]
        if not starts:
            msg = f"learning path has no numbered sections: {product}"
            raise ValueError(msg)
        prefix = text[: starts[0]].rstrip()
        boundaries = (*starts, len(text))
        kept: list[str] = []
        for start, end in pairwise(boundaries):
            section = text[start:end].strip()
            links = _LEARNING_LINK_RE.findall(section)
            if len(links) == 1 and links[0] in translated_routes:
                kept.append(section)
        if not kept:
            msg = f"learning path has no current translations: {product}"
            raise ValueError(msg)
        renumbered = [
            _LEARNING_SECTION_RE.sub(f"## {index}. ", section, count=1)
            for index, section in enumerate(kept, start=1)
        ]
        (destination / f"{product}.md").write_text(
            prefix + "\n\n" + "\n\n".join(renumbered) + "\n",
            encoding="utf-8",
            newline="\n",
        )


def _replace_content(content: Path, candidate: Path) -> None:
    backup = content.parent / f".content-backup-{uuid.uuid4().hex}"
    moved_live = False
    try:
        if content.exists():
            content.replace(backup)
            moved_live = True
        candidate.replace(content)
    except OSError:
        if content.exists():
            shutil.rmtree(content)
        if moved_live and backup.exists():
            backup.replace(content)
        raise
    if backup.exists():
        shutil.rmtree(backup)


def main() -> int:
    """Fetch all sources, preserve matching translations, and publish one snapshot."""
    root = Path(__file__).resolve().parents[2]
    manifest = load_sources(root / "source-ai" / "sources.yaml")
    content = root / "source-ai" / "content"
    cache_root = root / ".ai-local" / "english-fetch-cache"
    scratch = root / ".ai-local" / f"english-sync-{uuid.uuid4().hex}"
    candidate = scratch / "content"
    try:
        pages = _fetch_all(cache_root, manifest.root)
        translated = _populate_candidate(candidate, content, pages)
        validate_publishable_candidate(managed_root=candidate, manifest=manifest)
        _replace_content(content, candidate)
        if cache_root.exists():
            shutil.rmtree(cache_root)
    finally:
        if scratch.exists():
            shutil.rmtree(scratch)
    _ = sys.stdout.write(
        f"published {len(manifest.root)} English pages; "
        f"preserved {translated} translations\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
