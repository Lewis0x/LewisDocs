# Copyright 2026

"""Public bilingual content synchronization orchestration and CLI output."""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Final, NoReturn

from pydantic import SecretStr
from rich.console import Console
from rich.table import Table

from scripts.ai.errors import AIAgentError, ErrorCode
from scripts.ai.fetch import fetch_source
from scripts.ai.http_client import create_http_client
from scripts.ai.kimi import TranslationInput, translate_markdown
from scripts.ai.manifest import load_sources
from scripts.ai.normalize import normalize_source
from scripts.ai.pages import (
    parse_accepted_page,
    render_chinese_page,
    render_english_page,
    validate_candidate,
    validate_english_candidate,
)
from scripts.ai.snapshot import RealFileOps
from scripts.ai.sync_contracts import (
    AcceptanceRequest,
    ClientFactory,
    PageSyncResult,
    SyncDeps,
    SyncOptions,
    SyncReport,
    Translator,
    build_report,
    report_bytes,
)
from scripts.ai.sync_transaction import (
    replace_snapshot,
    validate_content_root,
    validate_support_paths,
    write_report,
)
from scripts.ai.types import SourceId  # noqa: TC001

if TYPE_CHECKING:
    import httpx2

    from scripts.ai.types import NormalizedPage, SourceManifest

__all__ = (
    "AcceptanceRequest",
    "ClientFactory",
    "PageSyncResult",
    "SyncDeps",
    "SyncOptions",
    "SyncReport",
    "Translator",
    "main",
    "replace_snapshot",
    "run_sync",
    "validate_content_root",
)

_ERROR_PRESENTATION: Final = {
    ErrorCode.MANIFEST_INVALID: (2, "manifest is invalid"),
    ErrorCode.FETCH_FAILED: (3, "source fetch failed"),
    ErrorCode.KEY_REQUIRED: (4, "translation key required"),
    ErrorCode.TRANSLATION_FAILED: (5, "translation failed"),
    ErrorCode.VALIDATION_FAILED: (6, "validation failed"),
    ErrorCode.WRITE_FAILED: (7, "write failed"),
}
_RESUME_ENV: Final = "AI_SYNC_RESUME"


def run_sync(options: SyncOptions, deps: SyncDeps) -> SyncReport:
    """Fetch, compare, translate changed pages, and accept one full candidate."""
    content_root = validate_content_root(options)
    validate_support_paths(options, content_root)
    manifest = load_sources(options.manifest_path)
    existing = _existing_pages(content_root, manifest)
    with deps.client_factory() as client:
        normalized = _fetch_all(manifest, client)
        report = build_report(manifest, normalized, existing)
        if report.result == "no_changes":
            validate_support_paths(options, content_root)
            write_report(options.report_path, report, deps.file_ops)
            return report
        key = os.environ.get("MOONSHOT_API_KEY")
        if key is None or not key.strip():
            first_changed = next(page for page in report.pages if page.changed)
            raise AIAgentError(
                code=ErrorCode.KEY_REQUIRED,
                message="translation key required",
                source_id=first_changed.source_id,
            )
        resume = os.environ.get(_RESUME_ENV) == "1"
        scratch = options.staging_root / ("resume" if resume else f"sync-{uuid.uuid4().hex}")
        try:
            candidate = _candidate(
                scratch,
                normalized,
                existing,
                key,
                client,
                deps,
                resume=resume,
            )
            validate_candidate(
                managed_root=candidate,
                learning_root=content_root / "learn",
                manifest=manifest,
            )
            replace_snapshot(
                AcceptanceRequest(options=options, candidate=candidate, report=report),
                deps.file_ops,
            )
        except AIAgentError as error:
            if scratch.exists() and not (resume and error.code == ErrorCode.TRANSLATION_FAILED):
                deps.file_ops.remove(scratch, fault=None)
            raise
    return report


def _existing_pages(
    content: Path,
    manifest: SourceManifest,
) -> dict[SourceId, tuple[bytes, bytes, str]]:
    english, chinese = content / "en", content / "zh-CN"
    if chinese.exists() and not english.exists():
        _validation_failed()
    if not english.exists():
        return {}
    if not chinese.exists():
        validate_english_candidate(managed_root=content, manifest=manifest)
        return {}
    validate_candidate(
        managed_root=content,
        learning_root=content / "learn",
        manifest=manifest,
    )
    return {
        source.id: (
            (english / source.product / f"{source.slug}.md").read_bytes(),
            (chinese / source.product / f"{source.slug}.md").read_bytes(),
            parse_accepted_page(english / source.product / f"{source.slug}.md").content_sha256,
        )
        for source in manifest.root
    }


def _fetch_all(
    manifest: SourceManifest,
    client: httpx2.Client,
) -> tuple[NormalizedPage, ...]:
    return tuple(
        normalize_source(source=source, fetched=fetch_source(client, source))
        for source in manifest.root
    )


def _candidate(  # noqa: PLR0913, PLR0917
    scratch: Path,
    pages: tuple[NormalizedPage, ...],
    existing: dict[SourceId, tuple[bytes, bytes, str]],
    key: str,
    client: httpx2.Client,
    deps: SyncDeps,
    *,
    resume: bool,
) -> Path:
    seed, candidate = scratch / "seed", scratch / "candidate"
    if candidate.exists():
        deps.file_ops.remove(candidate, fault=None)
    for page in pages:
        changed = (
            page.source.id not in existing or existing[page.source.id][2] != page.content_sha256
        )
        english = render_english_page(page) if changed else existing[page.source.id][0]
        cached = _cached_chinese(seed, page, english) if resume and changed else None
        chinese = (
            cached
            if cached is not None
            else _chinese(page, changed, existing, key, client, deps.translator)
        )
        deps.file_ops.write_bytes(
            seed / "en" / page.source.product / f"{page.source.slug}.md",
            english,
            fault=None,
        )
        deps.file_ops.write_bytes(
            seed / "zh-CN" / page.source.product / f"{page.source.slug}.md",
            chinese,
            fault=None,
        )
    deps.file_ops.copy_tree(seed / "en", candidate / "en", fault="candidate:en")
    deps.file_ops.copy_tree(seed / "zh-CN", candidate / "zh-CN", fault="candidate:zh-CN")
    return candidate


def _cached_chinese(
    seed: Path,
    page: NormalizedPage,
    english: bytes,
) -> bytes | None:
    english_path = seed / "en" / page.source.product / f"{page.source.slug}.md"
    chinese_path = seed / "zh-CN" / page.source.product / f"{page.source.slug}.md"
    try:
        if english_path.read_bytes() != english:
            return None
        chinese = chinese_path.read_bytes()
        accepted = parse_accepted_page(chinese_path)
    except (AIAgentError, OSError):
        return None
    if (
        accepted.source_id != page.source.id
        or accepted.product != page.source.product
        or accepted.lang != "zh-CN"
        or accepted.content_sha256 != page.content_sha256
        or accepted.translation_of != page.source.id
    ):
        return None
    return chinese


def _chinese(  # noqa: PLR0913, PLR0917
    page: NormalizedPage,
    changed: bool,  # noqa: FBT001
    existing: dict[SourceId, tuple[bytes, bytes, str]],
    key: str,
    client: httpx2.Client,
    translator: Translator,
) -> bytes:
    if not changed:
        return existing[page.source.id][1]
    translated = translator(
        client,
        TranslationInput(page.source.id, page.markdown, SecretStr(key)),
    )
    return render_chinese_page(page, translated)


def _validation_failed() -> NoReturn:
    raise AIAgentError(code=ErrorCode.VALIDATION_FAILED, message="content root is invalid")


def main() -> int:
    """Run manual synchronization with secret-safe terminal output."""
    try:
        report = run_sync(_default_options(), _default_deps())
    except AIAgentError as error:
        exit_code, message = _error_presentation(error.code)
        source_id = error.source_id if error.source_id is not None else "-"
        reason = f" reason={error.reason}" if error.reason is not None else ""
        _console().print(f"code={error.code} source_id={source_id} message={message}{reason}")
        return exit_code
    _print_report(report)
    return 0


def _default_options() -> SyncOptions:
    repo_root = Path(__file__).resolve().parents[2]
    return SyncOptions(
        repo_root=repo_root,
        content_root=repo_root / "source-ai" / "content",
        staging_root=repo_root / ".ai-local" / "staging",
        manifest_path=repo_root / "source-ai" / "sources.yaml",
        report_path=repo_root / ".ai-local" / "report.json",
    )


def _default_deps() -> SyncDeps:
    return SyncDeps(
        client_factory=create_http_client,
        translator=translate_markdown,
        file_ops=RealFileOps(),
    )


def _print_report(report: SyncReport) -> None:
    console = _console()
    if report.result == "no_changes":
        _ = sys.stdout.write("no changes\n")
    else:
        table = Table(
            "source_id",
            "old_sha256",
            "new_sha256",
            "changed",
            "translated",
            "result_code",
            box=None,
            pad_edge=False,
            padding=(0, 1),
        )
        for page in report.pages:
            table.add_row(
                page.source_id,
                page.old_sha256 or "-",
                page.new_sha256,
                str(page.changed).lower(),
                str(page.translated).lower(),
                page.result_code,
            )
        _ = console.print(table)
    _ = sys.stdout.write(report_bytes(report).decode("utf-8"))


def _console() -> Console:
    return Console(
        file=sys.stdout,
        force_terminal=False,
        color_system=None,
        width=160,
        highlight=False,
        markup=False,
    )


def _error_presentation(code: ErrorCode) -> tuple[int, str]:
    return _ERROR_PRESENTATION[code]
