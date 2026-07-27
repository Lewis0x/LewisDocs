# Copyright 2026

"""Private accepted-content materialization boundary."""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Final, NoReturn

from scripts.ai.errors import AIAgentError, ErrorCode
from scripts.ai.manifest import load_sources
from scripts.ai.pages import validate_candidate
from scripts.ai.sync_contracts import SyncOptions
from scripts.ai.sync_transaction import validate_private_root

if TYPE_CHECKING:
    from scripts.ai.types import SourceId

_FRONTMATTER_END: Final = b"\n---\n"


@dataclass(frozen=True, slots=True)
class MaterializeOptions:
    """Paths required to derive private AI documentation."""

    repo_root: Path
    content_root: Path
    docs_ai_root: Path
    manifest_path: Path


@dataclass(frozen=True, slots=True)
class MaterializedRoute:
    """One derived VitePress route."""

    source_id: SourceId | None
    lang: str
    route: str
    counterpart: str | None


@dataclass(frozen=True, slots=True)
class _SwapState:
    backed_up: bool
    promoted: bool


def materialize_ai(options: MaterializeOptions) -> tuple[MaterializedRoute, ...]:
    """Derive validated private content into the VitePress source tree."""
    content_root = _validated_content_root(options)
    manifest = load_sources(options.manifest_path)
    validate_candidate(
        managed_root=content_root,
        learning_root=content_root / "learn",
        manifest=manifest,
    )
    _require_derived_target(options)
    routes = tuple(
        MaterializedRoute(
            source_id=source.id,
            lang=lang,
            route=f"/ai/{lang}/{source.product}/{source.slug}",
            counterpart=f"/ai/{'zh-CN' if lang == 'en' else 'en'}/{source.product}/{source.slug}",
        )
        for source in manifest.root
        for lang in ("en", "zh-CN")
    ) + tuple(
        MaterializedRoute(
            source_id=None,
            lang="zh-CN",
            route=f"/ai/zh-CN/learn/{product}",
            counterpart=None,
        )
        for product in ("claude-code", "codex")
    )
    _replace_derived_tree(options, content_root, routes)
    return routes


def main() -> int:
    """Run materialization from the repository environment."""
    repo_root = Path(__file__).resolve().parents[2]
    content_value = os.environ.get("AI_CONTENT_ROOT")
    if content_value is None or not content_value.strip():
        _validation_failed()
    content_root = Path(content_value)
    if not content_root.is_absolute():
        _validation_failed()
    try:
        routes = materialize_ai(
            MaterializeOptions(
                repo_root=repo_root,
                content_root=content_root,
                docs_ai_root=repo_root / "docs" / "ai",
                manifest_path=repo_root / "source-ai" / "sources.yaml",
            )
        )
    except AIAgentError as error:
        _ = sys.stderr.write(f"{error.code}: AI handbook materialization failed\n")
        return 1
    _ = sys.stdout.write(f"materialized {len(routes)} AI handbook routes\n")
    return 0


def _validated_content_root(options: MaterializeOptions) -> Path:
    sync_options = SyncOptions(
        repo_root=options.repo_root,
        content_root=options.content_root,
        staging_root=options.repo_root / ".ai-local" / "staging",
        manifest_path=options.manifest_path,
        report_path=options.repo_root / ".ai-local" / "report.json",
    )
    return validate_private_root(sync_options)


def _require_derived_target(options: MaterializeOptions) -> None:
    expected = (options.repo_root / "docs" / "ai").resolve(strict=False)
    try:
        actual = options.docs_ai_root.resolve(strict=False)
    except OSError:
        _validation_failed()
    if actual != expected or options.docs_ai_root.is_symlink():
        _validation_failed()


def _replace_derived_tree(
    options: MaterializeOptions,
    content_root: Path,
    routes: tuple[MaterializedRoute, ...],
) -> None:
    target = options.docs_ai_root
    parent = target.parent
    try:
        parent.mkdir(parents=True, exist_ok=True)
        staged = Path(tempfile.mkdtemp(prefix=".ai-materialize-", dir=parent))
    except OSError:
        _write_failed()
    swap_id = uuid.uuid4().hex
    backup = parent / f".ai-backup-{swap_id}"
    retired = options.repo_root / ".ai-local" / f".ai-retired-{swap_id}"
    backed_up = False
    promoted = False
    try:
        _populate(staged, content_root, routes)
        if target.exists():
            _ = target.replace(backup)
            backed_up = True
        _ = staged.replace(target)
        promoted = True
    except OSError:
        _rollback(
            target,
            staged,
            backup,
            _SwapState(backed_up=backed_up, promoted=promoted),
        )
        _write_failed()
    if not backed_up:
        return
    try:
        retired.parent.mkdir(parents=True, exist_ok=True)
        _ = backup.replace(retired)
    except OSError:
        _rollback(
            target,
            staged,
            backup,
            _SwapState(backed_up=True, promoted=True),
        )
        _write_failed()
    try:
        shutil.rmtree(retired)
    except OSError:
        _write_failed()


def _populate(
    staged: Path,
    content_root: Path,
    routes: tuple[MaterializedRoute, ...],
) -> None:
    for item in routes:
        relative = item.route.removeprefix("/ai/")
        destination = staged / f"{relative}.md"
        destination.parent.mkdir(parents=True, exist_ok=True)
        if item.source_id is None:
            product = item.route.rsplit("/", maxsplit=1)[1]
            _ = shutil.copy2(
                content_root / "learn" / "zh-CN" / f"{product}.md",
                destination,
            )
            continue
        product, slug = str(item.source_id).split("/", maxsplit=1)
        source = content_root / item.lang / product / f"{slug}.md"
        _ = destination.write_bytes(_derive_source_page(source.read_bytes(), item))


def _derive_source_page(data: bytes, item: MaterializedRoute) -> bytes:
    closing = data.find(_FRONTMATTER_END, len(b"---\n"))
    if not data.startswith(b"---\n") or closing < 0 or item.counterpart is None:
        _validation_failed()
    fields = data[len(b"---\n") : closing].decode("utf-8").splitlines()
    title_key, separator, title = fields[0].partition(": ")
    if title_key != "title" or not separator or not title:
        _validation_failed()
    prefix = "EN · " if item.lang == "en" else "中文 · "
    label = "EN" if item.lang == "en" else "中文"
    derived = (
        f"---\ntitle: {prefix}{title}\n"
        + "\n".join(fields[1:])
        + f"\nai_counterpart: {item.counterpart}\nai_search_label: {label}"
    ).encode()
    return derived + data[closing:]


def _rollback(
    target: Path,
    staged: Path,
    backup: Path,
    state: _SwapState,
) -> None:
    try:
        if state.promoted and target.exists():
            shutil.rmtree(target)
        if state.backed_up and backup.exists():
            _ = backup.replace(target)
        if staged.exists():
            shutil.rmtree(staged)
    except OSError:
        _write_failed()


def _validation_failed() -> NoReturn:
    raise AIAgentError(
        code=ErrorCode.VALIDATION_FAILED,
        message="private content root is invalid",
    )


def _write_failed() -> NoReturn:
    raise AIAgentError(
        code=ErrorCode.WRITE_FAILED,
        message="AI handbook materialization failed",
    )


if __name__ == "__main__":
    raise SystemExit(main())
