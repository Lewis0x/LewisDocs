# Copyright 2026

"""Fetch, validate, and atomically apply owner-published Chinese pages."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Final

import httpx2

from scripts.ai.errors import AIAgentError
from scripts.ai.fetch import fetch_source
from scripts.ai.http_client import create_http_client
from scripts.ai.manifest import load_sources
from scripts.ai.normalize import normalize_source
from scripts.ai.official_localization import (
    official_chinese_urls,
    validate_official_localization,
)
from scripts.ai.pages import (
    parse_accepted_page,
    render_english_page,
    render_official_chinese_page,
    validate_publishable_candidate,
)

if TYPE_CHECKING:
    from scripts.ai.types import NormalizedPage, Source

_ENGLISH_PREFIX: Final = "[Official source]({url})\n\nContent owner: {owner}\n\n"
_FETCH_ATTEMPTS: Final = 3


class _RetryInvariantError(RuntimeError):
    """Signal an unreachable empty retry result."""


@dataclass(frozen=True, slots=True)
class SyncResult:
    """One official localization decision."""

    source_id: str
    status: str
    reason: str | None
    translation_url: str | None
    english_sha256: str | None
    localization_sha256: str | None
    english_updated: bool


@dataclass(frozen=True, slots=True)
class _PagePayload:
    source: Source
    english: bytes
    chinese: bytes


def main() -> int:
    """Run a point-in-time official localization refresh."""
    options = _parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    content_root = repo_root / "source-ai" / "content"
    selection_path = repo_root / "source-ai" / "official-localizations.json"
    report_path = repo_root / ".ai-local" / "official-chinese-sync-report.json"
    staging_root = repo_root / ".ai-local" / "staging" / "official-chinese-sync"
    try:
        source_ids = _load_selection(selection_path)
        manifest = load_sources(repo_root / "source-ai" / "sources.yaml")
        by_id = {str(source.id): source for source in manifest.root}
        payloads: dict[str, _PagePayload] = {}
        results: list[SyncResult] = []
        transport = httpx2.HTTPTransport(
            http2=False,
            retries=3,
            proxy=os.environ.get("LEWISDOCS_SYNC_PROXY") or None,
        )
        with create_http_client(transport=transport) as client:
            for source_id in source_ids:
                source = by_id[source_id]
                canonical_url: str | None = None
                live_english: NormalizedPage | None = None
                live_chinese: NormalizedPage | None = None
                local_english: str | None = None
                try:
                    canonical_url, fetch_url = official_chinese_urls(source)
                    live_english = _fetch_normalized(client, source)
                    localized_source = source.model_copy(
                        update={
                            "canonical_url": canonical_url,
                            "fetch_url": fetch_url,
                        }
                    )
                    live_chinese = _fetch_normalized(client, localized_source)
                    local_english = _local_english_markdown(content_root, source)
                    _write_fetched(
                        staging_root,
                        source_id,
                        "en",
                        live_english.markdown,
                    )
                    _write_fetched(
                        staging_root,
                        source_id,
                        "zh-CN",
                        live_chinese.markdown,
                    )
                    validate_official_localization(
                        live_english.markdown,
                        live_chinese.markdown,
                    )
                    payload = render_official_chinese_page(
                        live_english,
                        live_chinese.markdown,
                        translation_url=canonical_url,
                    )
                    parsed_path = _write_probe(staging_root, source_id, payload)
                    parsed = parse_accepted_page(parsed_path)
                    payloads[source_id] = _PagePayload(
                        source=source,
                        english=render_english_page(live_english),
                        chinese=payload,
                    )
                    results.append(
                        SyncResult(
                            source_id=source_id,
                            status="ready",
                            reason=None,
                            translation_url=canonical_url,
                            english_sha256=live_english.content_sha256,
                            localization_sha256=parsed.localization_sha256,
                            english_updated=local_english != live_english.markdown,
                        )
                    )
                except (AIAgentError, OSError, ValueError) as exc:
                    results.append(
                        SyncResult(
                            source_id=source_id,
                            status="skipped",
                            reason=_safe_reason(exc),
                            translation_url=canonical_url,
                            english_sha256=(
                                live_english.content_sha256
                                if live_english is not None
                                else None
                            ),
                            localization_sha256=(
                                live_chinese.content_sha256
                                if live_chinese is not None
                                else None
                            ),
                            english_updated=(
                                live_english is not None
                                and local_english is not None
                                and local_english != live_english.markdown
                            ),
                        )
                    )
        candidate = _prepare_candidate(
            content_root=content_root,
            staging_root=staging_root,
            payloads=payloads,
        )
        _ = validate_publishable_candidate(managed_root=candidate, manifest=manifest)
        if options.apply and payloads:
            _apply_candidate(
                content_root=content_root,
                candidate=candidate,
                staging_root=staging_root,
            )
        _write_report(
            report_path,
            apply=options.apply,
            results=results,
            applied=len(payloads) if options.apply else 0,
        )
    except (AIAgentError, KeyError, OSError, ValueError) as exc:
        _ = sys.stderr.write(f"{_safe_reason(exc)}\n")
        return 1
    ready = sum(result.status == "ready" for result in results)
    skipped = len(results) - ready
    action = "applied" if options.apply else "validated"
    _ = sys.stdout.write(f"{action} {ready} official Chinese pages; skipped {skipped}\n")
    return 0


@dataclass(frozen=True, slots=True)
class _Options:
    apply: bool


def _parse_args() -> _Options:
    parser = argparse.ArgumentParser()
    _ = parser.add_argument(
        "--apply",
        action="store_true",
        help="Atomically replace the accepted zh-CN tree after validation.",
    )
    args = parser.parse_args()
    return _Options(apply=bool(args.apply))


def _load_selection(path: Path) -> tuple[str, ...]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if (
        not isinstance(raw, dict)
        or raw.get("schema_version") != 1
        or raw.get("provider") != "Anthropic"
        or raw.get("locale") != "zh-CN"
        or raw.get("validation_policy") != "strict-current-content"
    ):
        message = "official localization selection is invalid"
        raise ValueError(message)
    source_ids = raw.get("source_ids")
    if (
        not isinstance(source_ids, list)
        or not source_ids
        or any(not isinstance(item, str) or not item for item in source_ids)
        or len(source_ids) != len(set(source_ids))
    ):
        message = "official localization source_ids are invalid"
        raise ValueError(message)
    return tuple(source_ids)


def _local_english_markdown(content_root: Path, source: Source) -> str:
    page = parse_accepted_page(
        content_root / "en" / source.product / f"{source.slug}.md"
    )
    prefix = _ENGLISH_PREFIX.format(url=source.canonical_url, owner=source.owner)
    if page.source_id != source.id or not page.body.startswith(prefix):
        message = "local English page metadata is invalid"
        raise ValueError(message)
    return page.body.removeprefix(prefix)


def _fetch_normalized(client: httpx2.Client, source: Source) -> NormalizedPage:
    last_error: AIAgentError | None = None
    for attempt in range(_FETCH_ATTEMPTS):
        try:
            return normalize_source(
                source=source,
                fetched=fetch_source(client, source),
            )
        except AIAgentError as exc:
            last_error = exc
            if attempt < _FETCH_ATTEMPTS - 1:
                time.sleep(2**attempt)
    if last_error is None:
        raise _RetryInvariantError
    raise last_error


def _write_probe(staging_root: Path, source_id: str, payload: bytes) -> Path:
    path = staging_root / "probes" / f"{source_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return path


def _write_fetched(
    staging_root: Path,
    source_id: str,
    language: str,
    markdown: str,
) -> Path:
    path = staging_root / "fetched" / language / f"{source_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown, encoding="utf-8", newline="\n")
    return path


def _prepare_candidate(
    *,
    content_root: Path,
    staging_root: Path,
    payloads: dict[str, _PagePayload],
) -> Path:
    candidate = staging_root / "candidate"
    if candidate.exists():
        shutil.rmtree(candidate)
    shutil.copytree(content_root, candidate)
    for payload in payloads.values():
        for language, data in (
            ("en", payload.english),
            ("zh-CN", payload.chinese),
        ):
            destination = (
                candidate
                / language
                / payload.source.product
                / f"{payload.source.slug}.md"
            )
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
    return candidate


def _apply_candidate(
    *,
    content_root: Path,
    candidate: Path,
    staging_root: Path,
) -> None:
    nonce = uuid.uuid4().hex
    backup = (
        staging_root
        / "backups"
        / f"{datetime.now(tz=UTC).strftime('%Y%m%dT%H%M%SZ')}-{nonce}"
    )
    backup.mkdir(parents=True, exist_ok=False)
    languages = ("en", "zh-CN")
    next_trees = {
        language: content_root.parent / f".{language}-official-next-{nonce}"
        for language in languages
    }
    moved_live: set[str] = set()
    promoted: set[str] = set()
    for language, next_tree in next_trees.items():
        shutil.copytree(candidate / language, next_tree)
    try:
        for language in languages:
            live = content_root / language
            if live.exists():
                live.replace(backup / language)
                moved_live.add(language)
        for language in languages:
            next_trees[language].replace(content_root / language)
            promoted.add(language)
    except OSError:
        for language in reversed(languages):
            live = content_root / language
            if language in promoted and live.exists():
                shutil.rmtree(live)
            if language in moved_live and (backup / language).exists():
                (backup / language).replace(live)
            next_tree = next_trees[language]
            if next_tree.exists():
                shutil.rmtree(next_tree)
        raise


def _write_report(
    path: Path,
    *,
    apply: bool,
    results: list[SyncResult],
    applied: int,
) -> None:
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "mode": "apply" if apply else "validate",
        "ready": sum(result.status == "ready" for result in results),
        "skipped": sum(result.status == "skipped" for result in results),
        "applied": applied,
        "results": [asdict(result) for result in results],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _safe_reason(exc: Exception) -> str:
    if isinstance(exc, AIAgentError):
        source = f" ({exc.source_id})" if exc.source_id is not None else ""
        return f"{exc.code}{source}"
    text = str(exc).strip()
    return text or type(exc).__name__


if __name__ == "__main__":
    raise SystemExit(main())
