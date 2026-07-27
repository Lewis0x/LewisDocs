# Copyright 2026

"""Synchronization contracts and canonical report serialization."""

from __future__ import annotations

import json
from contextlib import AbstractContextManager  # noqa: TC003
from dataclasses import dataclass
from pathlib import Path  # noqa: TC003
from typing import TYPE_CHECKING, ClassVar, Literal, Protocol

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from scripts.ai.kimi import TranslationInput  # noqa: TC001
from scripts.ai.types import SourceId  # noqa: TC001

if TYPE_CHECKING:
    import httpx2

    from scripts.ai.snapshot import FileOps
    from scripts.ai.types import NormalizedPage, SourceManifest

_HASH_LENGTH = 64
_HASH_ERROR = "hash must be SHA-256"
_NO_CHANGE_ERROR = "no-change result is inconsistent"
_UPDATED_ERROR = "updated result is inconsistent"
_REPORT_ERROR = "report result is inconsistent"


class PageSyncResult(BaseModel):
    """One source-level result in deterministic manifest order."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid", strict=True)

    source_id: SourceId
    old_sha256: str | None
    new_sha256: str
    changed: bool
    translated: bool
    result_code: Literal["NO_CHANGES", "UPDATED"]

    @field_validator("old_sha256", "new_sha256")
    @classmethod
    def _valid_hash(cls, value: str | None) -> str | None:
        if value is not None and len(value) != _HASH_LENGTH:
            raise ValueError(_HASH_ERROR)
        if value is not None and any(character not in "0123456789abcdef" for character in value):
            raise ValueError(_HASH_ERROR)
        return value

    @model_validator(mode="after")
    def _consistent(self) -> PageSyncResult:
        if self.result_code == "NO_CHANGES":
            if self.changed or self.translated or self.old_sha256 != self.new_sha256:
                raise ValueError(_NO_CHANGE_ERROR)
        elif not self.changed or not self.translated or self.old_sha256 == self.new_sha256:
            raise ValueError(_UPDATED_ERROR)
        return self


class SyncReport(BaseModel):
    """Secret-free JSON-safe result of one synchronization."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid", strict=True)

    result: Literal["no_changes", "updated"]
    pages: tuple[PageSyncResult, ...]

    @model_validator(mode="after")
    def _consistent(self) -> SyncReport:
        any_changed = any(page.result_code == "UPDATED" for page in self.pages)
        if (self.result == "updated") != any_changed:
            raise ValueError(_REPORT_ERROR)
        return self


class SyncOptions(BaseModel):
    """Resolved local locations required by the synchronization boundary."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid", strict=True)

    repo_root: Path
    content_root: Path
    staging_root: Path
    manifest_path: Path
    report_path: Path


class ClientFactory(Protocol):
    """Creates a managed source/translation HTTP client."""

    def __call__(self) -> AbstractContextManager[httpx2.Client]: ...  # noqa: D102


class Translator(Protocol):
    """Translates one normalized Markdown page with the supplied client."""

    def __call__(self, client: httpx2.Client, request: TranslationInput) -> str: ...  # noqa: D102


@dataclass(frozen=True, slots=True)
class SyncDeps:
    """Narrow capabilities supplied by the outer application layer."""

    client_factory: ClientFactory
    translator: Translator
    file_ops: FileOps


@dataclass(frozen=True, slots=True)
class AcceptanceRequest:
    """Already-validated candidate and report accepted as one transaction."""

    options: SyncOptions
    candidate: Path
    report: SyncReport


def build_report(
    manifest: SourceManifest,
    pages: tuple[NormalizedPage, ...],
    existing: dict[SourceId, tuple[bytes, bytes, str]],
) -> SyncReport:
    """Build one manifest-ordered report from fetched and accepted hashes."""
    results = tuple(
        PageSyncResult(
            source_id=source.id,
            old_sha256=existing[source.id][2] if source.id in existing else None,
            new_sha256=page.content_sha256,
            changed=source.id not in existing or existing[source.id][2] != page.content_sha256,
            translated=source.id not in existing or existing[source.id][2] != page.content_sha256,
            result_code="UPDATED"
            if source.id not in existing or existing[source.id][2] != page.content_sha256
            else "NO_CHANGES",
        )
        for source, page in zip(manifest.root, pages, strict=True)
    )
    return SyncReport(
        result="updated" if any(item.changed for item in results) else "no_changes",
        pages=results,
    )


def report_bytes(report: SyncReport) -> bytes:
    """Serialize the canonical secret-free report JSON bytes."""
    return (
        json.dumps(
            report.model_dump(mode="json"),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
