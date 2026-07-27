# Copyright 2026

"""Deterministic content snapshots and local filesystem operations."""

from __future__ import annotations

import pathlib
from dataclasses import dataclass
from hashlib import sha256
from os import DirEntry, scandir
from shutil import Error as CopyTreeError
from shutil import copytree, rmtree
from typing import TYPE_CHECKING, Protocol

from scripts.ai.errors import AIAgentError, ErrorCode

if TYPE_CHECKING:
    from collections.abc import Iterator


@dataclass(frozen=True, slots=True)
class FileDigest:
    """A SHA-256 digest for one POSIX-relative file path."""

    path: str
    sha256: str


@dataclass(frozen=True, slots=True)
class Snapshot:
    """An ordered, immutable view of a directory tree's file digests."""

    files: tuple[FileDigest, ...]


class FileOps(Protocol):
    """Narrow filesystem boundary used by the acceptance transaction."""

    def copy_tree(self, source: pathlib.Path, destination: pathlib.Path, fault: str | None) -> None:
        """Copy a directory tree without overwriting its destination."""

    def replace(self, source: pathlib.Path, destination: pathlib.Path, fault: str | None) -> None:
        """Replace one path with another on the same filesystem."""

    def write_bytes(self, path: pathlib.Path, data: bytes, fault: str | None) -> None:
        """Write exact bytes, creating parent directories as needed."""

    def remove(self, path: pathlib.Path, fault: str | None) -> None:
        """Remove exactly the supplied file, link, or tree."""


class RealFileOps:
    """Production filesystem implementation of :class:`FileOps`."""

    def copy_tree(self, source: pathlib.Path, destination: pathlib.Path, fault: str | None) -> None:
        """Copy a directory tree without overwriting its destination."""
        del fault
        try:
            _ = copytree(source, destination)
        except (CopyTreeError, OSError):
            raise _write_failure() from None

    def replace(self, source: pathlib.Path, destination: pathlib.Path, fault: str | None) -> None:
        """Replace one path with another on the same filesystem."""
        del fault
        try:
            _ = source.replace(destination)
        except OSError:
            raise _write_failure() from None

    def write_bytes(self, path: pathlib.Path, data: bytes, fault: str | None) -> None:
        """Write exact bytes, creating parent directories as needed."""
        del fault
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            _ = path.write_bytes(data)
        except OSError:
            raise _write_failure() from None

    def remove(self, path: pathlib.Path, fault: str | None) -> None:
        """Remove exactly the supplied file, link, or tree."""
        del fault
        try:
            if path.is_symlink() or path.is_file():
                path.unlink()
            elif path.is_dir():
                _ = rmtree(path)
            elif path.exists():
                raise _write_failure()
        except OSError:
            raise _write_failure() from None


def tree_snapshot(root: pathlib.Path) -> Snapshot:
    """Return the deterministic file snapshot for ``root``."""
    try:
        if root.is_symlink() or not root.is_dir():
            raise AIAgentError(
                code=ErrorCode.VALIDATION_FAILED,
                message="snapshot root must be a real directory",
            )
        paths = tuple(sorted(_iter_regular_files(root), key=lambda path: path.as_posix()))
        return Snapshot(
            files=tuple(
                FileDigest(
                    path=path.relative_to(root).as_posix(),
                    sha256=sha256(path.read_bytes()).hexdigest(),
                )
                for path in paths
            )
        )
    except OSError:
        raise AIAgentError(
            code=ErrorCode.VALIDATION_FAILED,
            message="snapshot tree is unreadable",
        ) from None


def _iter_regular_files(directory: pathlib.Path) -> Iterator[pathlib.Path]:
    with scandir(directory) as entries:
        for entry in entries:
            yield from _paths_for_entry(entry)


def _paths_for_entry(entry: DirEntry[str]) -> Iterator[pathlib.Path]:
    if entry.is_symlink():
        raise AIAgentError(
            code=ErrorCode.VALIDATION_FAILED,
            message="snapshot tree cannot contain symbolic links",
        )
    if entry.is_dir(follow_symlinks=False):
        yield from _iter_regular_files(pathlib.Path(entry.path))
        return
    if entry.is_file(follow_symlinks=False):
        yield pathlib.Path(entry.path)
        return
    raise AIAgentError(
        code=ErrorCode.VALIDATION_FAILED,
        message="snapshot tree must contain only regular files",
    )


def _write_failure() -> AIAgentError:
    return AIAgentError(
        code=ErrorCode.WRITE_FAILED,
        message="filesystem operation failed",
    )
