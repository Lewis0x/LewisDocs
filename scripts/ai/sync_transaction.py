# Copyright 2026

"""Public content-root validation and atomic accepted-snapshot transactions."""

from __future__ import annotations

import subprocess
import uuid
from dataclasses import dataclass
from dataclasses import replace as dataclass_replace
from pathlib import Path
from typing import TYPE_CHECKING, NoReturn

from scripts.ai.errors import AIAgentError, ErrorCode
from scripts.ai.sync_contracts import AcceptanceRequest, SyncOptions, SyncReport, report_bytes

if TYPE_CHECKING:
    from scripts.ai.snapshot import FileOps


def validate_content_root(options: SyncOptions) -> Path:
    """Return the fixed public root or a legacy external/ignored content root."""
    if not options.content_root.is_absolute():
        _validation_failed()
    try:
        repo = options.repo_root.resolve(strict=False)
        content = options.content_root.resolve(strict=False)
    except OSError:
        _validation_failed()
    try:
        relative = content.relative_to(repo)
    except ValueError:
        return content
    if relative == Path("source-ai", "content"):
        return content
    if relative == Path() or relative.parts[0] != ".ai-content":
        _validation_failed()
    _require_ignored_untracked(repo, relative)
    return content


def validate_support_paths(options: SyncOptions, content: Path) -> None:
    """Reject support paths that are unsafe or overlap private content."""
    report = _resolve_support(options.repo_root, options.report_path)
    staging = _resolve_support(options.repo_root, options.staging_root)
    if report == staging or _contains(content, report) or _contains(content, staging):
        _validation_failed()
    if _contains(report, content) or _contains(staging, content):
        _validation_failed()


def _resolve_support(repo_root: Path, path: Path) -> Path:
    if not path.is_absolute():
        _validation_failed()
    try:
        repo = repo_root.resolve(strict=False)
        resolved = path.resolve(strict=False)
    except OSError:
        _validation_failed()
    try:
        relative = resolved.relative_to(repo)
    except ValueError:
        return resolved
    if relative == Path() or relative.parts[0] != ".ai-local":
        _validation_failed()
    _require_ignored_untracked(repo, relative)
    return resolved


def _contains(parent: Path, child: Path) -> bool:
    try:
        _ = child.relative_to(parent)
    except ValueError:
        return False
    return True


def _require_ignored_untracked(repo: Path, relative: Path) -> None:
    ignored = _git_status(repo, ["check-ignore", "--no-index", "-q", "--", relative.as_posix()])
    tracked = _git_status(repo, ["ls-files", "--error-unmatch", "--", relative.as_posix()])
    if ignored != 0 or tracked == 0 or tracked > 1:
        _validation_failed()


def _git_status(repo: Path, arguments: list[str]) -> int:
    try:
        return subprocess.run(  # noqa: S603
            ["git", *arguments],  # noqa: S607
            cwd=repo,
            check=False,
            shell=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode
    except OSError:
        _validation_failed()


def replace_snapshot(request: AcceptanceRequest, file_ops: FileOps) -> None:
    """Swap paired trees and report while retaining rollback sources."""
    content = validate_content_root(request.options)
    validate_support_paths(request.options, content)
    nonce = uuid.uuid4().hex
    parent = content.parent
    next_en, next_zh = parent / f".en-next-{nonce}", parent / f".zh-CN-next-{nonce}"
    backup_en, backup_zh = parent / f".en-backup-{nonce}", parent / f".zh-CN-backup-{nonce}"
    report = request.options.report_path
    report_backup = report.parent / f".{report.name}.backup-{nonce}"
    report_temp = report.parent / f".{report.name}.temp-{nonce}"
    live_en, live_zh = content / "en", content / "zh-CN"
    state = _AcceptanceState(live_en.exists(), live_zh.exists(), report.exists())
    try:
        file_ops.copy_tree(request.candidate / "en", next_en, fault="next:en")
        file_ops.copy_tree(request.candidate / "zh-CN", next_zh, fault="next:zh-CN")
        if state.had_en:
            file_ops.replace(live_en, backup_en, fault="rename:en-live-to-backup")
            state = dataclass_replace(state, en_backed_up=True)
        if state.had_zh:
            file_ops.replace(live_zh, backup_zh, fault="rename:zh-CN-live-to-backup")
            state = dataclass_replace(state, zh_backed_up=True)
        file_ops.replace(next_en, live_en, fault="rename:en-next-to-live")
        state = dataclass_replace(state, en_promoted=True)
        file_ops.replace(next_zh, live_zh, fault="rename:zh-CN-next-to-live")
        state = dataclass_replace(state, zh_promoted=True)
        if state.had_report:
            file_ops.replace(report, report_backup, fault=None)
            state = dataclass_replace(state, report_backed_up=True)
        file_ops.write_bytes(report_temp, report_bytes(request.report), fault="report:temp-write")
        file_ops.replace(report_temp, report, fault="report:replace")
        state = dataclass_replace(state, report_promoted=True)
        _cleanup((backup_en, backup_zh, report_backup, request.candidate.parent), file_ops)
    except AIAgentError:
        _rollback(
            state,
            live_en,
            live_zh,
            backup_en,
            backup_zh,
            report,
            report_backup,
            report_temp,
            next_en,
            next_zh,
            request.candidate.parent,
            file_ops,
        )
        raise


@dataclass(frozen=True, slots=True)
class _AcceptanceState:
    had_en: bool
    had_zh: bool
    had_report: bool
    en_backed_up: bool = False
    zh_backed_up: bool = False
    report_backed_up: bool = False
    en_promoted: bool = False
    zh_promoted: bool = False
    report_promoted: bool = False


def write_report(path: Path, report: SyncReport, file_ops: FileOps) -> None:
    """Atomically replace a no-op report while restoring a prior report on failure."""
    nonce = uuid.uuid4().hex
    temp, backup = (
        path.parent / f".{path.name}.temp-{nonce}",
        path.parent / f".{path.name}.backup-{nonce}",
    )
    had_report = path.exists()
    try:
        if had_report:
            file_ops.replace(path, backup, fault=None)
        file_ops.write_bytes(temp, report_bytes(report), fault="report:temp-write")
        file_ops.replace(temp, path, fault="report:replace")
        if had_report:
            file_ops.remove(backup, fault="cleanup")
    except AIAgentError:
        if path.exists() and had_report:
            file_ops.remove(path, fault=None)
        if backup.exists():
            file_ops.replace(backup, path, fault=None)
        if temp.exists():
            file_ops.remove(temp, fault=None)
        raise


def _cleanup(paths: tuple[Path, ...], file_ops: FileOps) -> None:
    for index, path in enumerate(paths):
        if path.exists():
            file_ops.remove(path, fault="cleanup" if index == 0 else None)


def _rollback(  # noqa: PLR0913, PLR0917
    state: _AcceptanceState,
    live_en: Path,
    live_zh: Path,
    backup_en: Path,
    backup_zh: Path,
    report: Path,
    report_backup: Path,
    report_temp: Path,
    next_en: Path,
    next_zh: Path,
    scratch: Path,
    file_ops: FileOps,
) -> None:
    if state.en_promoted and live_en.exists():
        file_ops.remove(live_en, fault=None)
    if state.zh_promoted and live_zh.exists():
        file_ops.remove(live_zh, fault=None)
    if state.en_backed_up and backup_en.exists():
        file_ops.replace(backup_en, live_en, fault=None)
    if state.zh_backed_up and backup_zh.exists():
        file_ops.replace(backup_zh, live_zh, fault=None)
    if state.report_promoted and report.exists():
        file_ops.remove(report, fault=None)
    if state.report_backed_up and report_backup.exists():
        file_ops.replace(report_backup, report, fault=None)
    for path in (report_temp, next_en, next_zh, scratch):
        if path.exists():
            file_ops.remove(path, fault=None)


def _validation_failed() -> NoReturn:
    raise AIAgentError(code=ErrorCode.VALIDATION_FAILED, message="content root is invalid")
